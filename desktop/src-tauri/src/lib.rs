//! Throughline desktop shell.
//!
//! Lifts three browser ceilings the web MVP cannot fix:
//! 1. CORS — native HTTP from Rust reaches every provider / enterprise gateway
//! 2. Disk — notebooks live in a folder the user owns
//! 3. Keychain — API keys leave the tab and enter the OS secret store

use futures_util::StreamExt;
use keyring::Entry;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use tauri::ipc::Channel;
use tauri::Manager;

const SERVICE: &str = "org.throughline.desktop";

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FetchRequest {
  url: String,
  method: Option<String>,
  headers: Option<HashMap<String, String>>,
  body: Option<String>,
  /// Ask for the response as bytes rather than text. The streaming path below
  /// decodes with `from_utf8_lossy`, which is right for SSE and NDJSON and
  /// destroys a PNG. Image endpoints set this and get back one `done` chunk
  /// carrying a `data:` URL.
  binary: Option<bool>,
}

/// Base64 by hand rather than a dependency — it is eleven lines and this is
/// the only place in the app that needs it.
fn base64(bytes: &[u8]) -> String {
  const A: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let mut out = String::with_capacity((bytes.len() + 2) / 3 * 4);
  for c in bytes.chunks(3) {
    let b = [c[0], *c.get(1).unwrap_or(&0), *c.get(2).unwrap_or(&0)];
    let n = ((b[0] as u32) << 16) | ((b[1] as u32) << 8) | b[2] as u32;
    out.push(A[(n >> 18 & 63) as usize] as char);
    out.push(A[(n >> 12 & 63) as usize] as char);
    out.push(if c.len() > 1 { A[(n >> 6 & 63) as usize] as char } else { '=' });
    out.push(if c.len() > 2 { A[(n & 63) as usize] as char } else { '=' });
  }
  out
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct FetchChunk {
  kind: String, // "meta" | "text" | "done" | "error"
  status: Option<u16>,
  text: Option<String>,
  error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct Caps {
  shell: String,
  cors: bool,
  disk: bool,
  keychain: bool,
  /// True when running inside the Mac App Store App Sandbox container.
  sandboxed: bool,
  /// Human-readable library root hint for UI copy.
  library_hint: String,
  version: String,
}

/// App Sandbox sets this when the process is contained (Mac App Store builds).
fn is_sandboxed() -> bool {
  std::env::var_os("APP_SANDBOX_CONTAINER_ID").is_some()
}

fn library_config_path() -> Result<PathBuf, String> {
  let dir = dirs::data_dir()
    .ok_or_else(|| "no data dir".to_string())?
    .join("throughline");
  fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
  Ok(dir.join("library-root.json"))
}

fn load_library_root_override() -> Option<PathBuf> {
  let path = library_config_path().ok()?;
  let raw = fs::read_to_string(path).ok()?;
  let value: serde_json::Value = serde_json::from_str(&raw).ok()?;
  value
    .get("path")
    .and_then(|v| v.as_str())
    .map(PathBuf::from)
    .filter(|p| p.is_absolute())
}

fn save_library_root_override(path: &Path) -> Result<(), String> {
  let cfg = library_config_path()?;
  let body = serde_json::json!({ "path": path.to_string_lossy() });
  fs::write(cfg, serde_json::to_string_pretty(&body).unwrap()).map_err(|e| e.to_string())
}

fn resolve_library_root() -> Result<PathBuf, String> {
  if let Some(override_path) = load_library_root_override() {
    return Ok(override_path);
  }
  // Sandboxed MAS builds: NSDocumentDirectory is the container Documents
  // (writable). Direct-distribution builds: real ~/Documents.
  let dir = dirs::document_dir()
    .or_else(dirs::home_dir)
    .ok_or_else(|| "could not resolve Documents".to_string())?
    .join("Throughline");
  Ok(dir)
}

fn key_entry(provider: &str) -> Result<Entry, String> {
  Entry::new(SERVICE, &format!("provider:{provider}")).map_err(|e| e.to_string())
}

#[tauri::command]
fn desktop_caps() -> Caps {
  let sandboxed = is_sandboxed();
  let library_hint = resolve_library_root()
    .map(|p| p.to_string_lossy().into_owned())
    .unwrap_or_else(|_| {
      if sandboxed {
        "App Library (sandboxed)".into()
      } else {
        "~/Documents/Throughline".into()
      }
    });
  Caps {
    shell: "desktop".into(),
    cors: true,
    disk: true,
    keychain: true,
    sandboxed,
    library_hint,
    version: env!("CARGO_PKG_VERSION").into(),
  }
}

#[tauri::command]
fn save_secret(provider: String, secret: String) -> Result<(), String> {
  if provider.trim().is_empty() {
    return Err("provider required".into());
  }
  if secret.is_empty() {
    let _ = delete_secret(provider);
    return Ok(());
  }
  key_entry(&provider)?
    .set_password(&secret)
    .map_err(|e| e.to_string())
}

#[tauri::command]
fn load_secret(provider: String) -> Result<Option<String>, String> {
  match key_entry(&provider)?.get_password() {
    Ok(s) => Ok(Some(s)),
    Err(keyring::Error::NoEntry) => Ok(None),
    Err(e) => Err(e.to_string()),
  }
}

#[tauri::command]
fn delete_secret(provider: String) -> Result<(), String> {
  match key_entry(&provider)?.delete_credential() {
    Ok(()) => Ok(()),
    Err(keyring::Error::NoEntry) => Ok(()),
    Err(e) => Err(e.to_string()),
  }
}

#[tauri::command]
fn list_secrets() -> Result<Vec<String>, String> {
  // keyring has no enumerate API that is portable — we persist an index file.
  let path = secrets_index_path()?;
  if !path.exists() {
    return Ok(vec![]);
  }
  let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
  let list: Vec<String> = serde_json::from_str(&raw).unwrap_or_default();
  Ok(list)
}

fn secrets_index_path() -> Result<PathBuf, String> {
  let dir = dirs::data_dir()
    .ok_or_else(|| "no data dir".to_string())?
    .join("throughline");
  fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
  Ok(dir.join("secret-index.json"))
}

fn remember_secret_id(provider: &str) -> Result<(), String> {
  let path = secrets_index_path()?;
  let mut list: Vec<String> = if path.exists() {
    serde_json::from_str(&fs::read_to_string(&path).unwrap_or_default()).unwrap_or_default()
  } else {
    vec![]
  };
  if !list.iter().any(|p| p == provider) {
    list.push(provider.to_string());
    fs::write(&path, serde_json::to_string_pretty(&list).unwrap()).map_err(|e| e.to_string())?;
  }
  Ok(())
}

fn forget_secret_id(provider: &str) -> Result<(), String> {
  let path = secrets_index_path()?;
  if !path.exists() {
    return Ok(());
  }
  let mut list: Vec<String> =
    serde_json::from_str(&fs::read_to_string(&path).unwrap_or_default()).unwrap_or_default();
  list.retain(|p| p != provider);
  fs::write(&path, serde_json::to_string_pretty(&list).unwrap()).map_err(|e| e.to_string())?;
  Ok(())
}

#[tauri::command]
fn save_secret_tracked(provider: String, secret: String) -> Result<(), String> {
  save_secret(provider.clone(), secret.clone())?;
  if secret.is_empty() {
    forget_secret_id(&provider)?;
  } else {
    remember_secret_id(&provider)?;
  }
  Ok(())
}

#[tauri::command]
async fn native_fetch(req: FetchRequest, on_chunk: Channel<FetchChunk>) -> Result<(), String> {
  let method = req.method.unwrap_or_else(|| "GET".into());
  let client = reqwest::Client::builder()
    .user_agent(format!("Throughline-Desktop/{}", env!("CARGO_PKG_VERSION")))
    .build()
    .map_err(|e| e.to_string())?;

  let mut builder = match method.to_uppercase().as_str() {
    "POST" => client.post(&req.url),
    "PUT" => client.put(&req.url),
    "PATCH" => client.patch(&req.url),
    "DELETE" => client.delete(&req.url),
    _ => client.get(&req.url),
  };

  if let Some(headers) = &req.headers {
    for (k, v) in headers {
      builder = builder.header(k, v);
    }
  }
  if let Some(body) = &req.body {
    builder = builder.body(body.clone());
  }

  let res = builder.send().await.map_err(|e| e.to_string())?;
  let status = res.status().as_u16();
  let _ = on_chunk.send(FetchChunk {
    kind: "meta".into(),
    status: Some(status),
    text: None,
    error: None,
  });

  if !res.status().is_success() {
    let text = res.text().await.unwrap_or_default();
    let _ = on_chunk.send(FetchChunk {
      kind: "error".into(),
      status: Some(status),
      text: Some(text.chars().take(800).collect()),
      error: Some(format!("HTTP {status}")),
    });
    return Err(format!("HTTP {status}"));
  }

  if req.binary.unwrap_or(false) {
    let mime = res
      .headers()
      .get(reqwest::header::CONTENT_TYPE)
      .and_then(|v| v.to_str().ok())
      .unwrap_or("application/octet-stream")
      .split(';')
      .next()
      .unwrap_or("application/octet-stream")
      .to_string();
    let bytes = res.bytes().await.map_err(|e| e.to_string())?;
    let _ = on_chunk.send(FetchChunk {
      kind: "done".into(),
      status: Some(status),
      text: Some(format!("data:{};base64,{}", mime, base64(&bytes))),
      error: None,
    });
    return Ok(());
  }

  let mut stream = res.bytes_stream();
  let mut buf = String::new();
  while let Some(item) = stream.next().await {
    let bytes = item.map_err(|e| e.to_string())?;
    let piece = String::from_utf8_lossy(&bytes);
    buf.push_str(&piece);
    // Emit growing text for SSE/NDJSON consumers on the JS side.
    let _ = on_chunk.send(FetchChunk {
      kind: "text".into(),
      status: Some(status),
      text: Some(buf.clone()),
      error: None,
    });
  }

  let _ = on_chunk.send(FetchChunk {
    kind: "done".into(),
    status: Some(status),
    text: Some(buf),
    error: None,
  });
  Ok(())
}

fn ensure_library_layout(dir: &Path) -> Result<(), String> {
  fs::create_dir_all(dir).map_err(|e| e.to_string())?;
  fs::create_dir_all(dir.join("notebooks")).map_err(|e| e.to_string())?;
  fs::create_dir_all(dir.join("runs")).map_err(|e| e.to_string())?;
  let readme = dir.join("README.txt");
  if !readme.exists() {
    let note = if is_sandboxed() {
      "Throughline library folder (Mac App Store / sandboxed build)\n\n\
notebooks/  — your notebooks as JSON files\n\
runs/       — exported run transcripts\n\n\
This folder lives inside the app sandbox container. Use “Open library folder”\n\
in Throughline to reveal it in Finder. The website never sees these files.\n"
    } else {
      "Throughline library folder\n\n\
notebooks/  — your notebooks as JSON files (git-able, yours)\n\
runs/       — exported run transcripts\n\n\
The desktop app reads and writes here. The website never sees these files.\n"
    };
    let _ = fs::write(&readme, note);
  }
  Ok(())
}

#[tauri::command]
fn default_library_dir() -> Result<String, String> {
  let dir = resolve_library_root()?;
  ensure_library_layout(&dir)?;
  Ok(dir.to_string_lossy().into_owned())
}

/// Persist a user-chosen library root (requires user-selected file entitlement
/// under App Sandbox; pick the folder via the system dialog first).
#[tauri::command]
fn set_library_dir(path: String) -> Result<String, String> {
  let dir = PathBuf::from(path.trim());
  if !dir.is_absolute() {
    return Err("library path must be absolute".into());
  }
  ensure_library_layout(&dir)?;
  save_library_root_override(&dir)?;
  Ok(dir.to_string_lossy().into_owned())
}

#[tauri::command]
fn ensure_dir(path: String) -> Result<(), String> {
  fs::create_dir_all(Path::new(&path)).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_text_file(path: String, contents: String) -> Result<(), String> {
  if let Some(parent) = Path::new(&path).parent() {
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
  }
  let mut f = fs::File::create(&path).map_err(|e| e.to_string())?;
  f.write_all(contents.as_bytes()).map_err(|e| e.to_string())
}

#[tauri::command]
fn read_text_file(path: String) -> Result<String, String> {
  fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
fn list_json_files(dir: String) -> Result<Vec<String>, String> {
  let mut out = vec![];
  let rd = fs::read_dir(&dir).map_err(|e| e.to_string())?;
  for entry in rd.flatten() {
    let p = entry.path();
    if p.extension().and_then(|e| e.to_str()) == Some("json") {
      out.push(p.to_string_lossy().into_owned());
    }
  }
  out.sort();
  Ok(out)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_opener::init())
    .plugin(tauri_plugin_dialog::init())
    .plugin(tauri_plugin_fs::init())
    .invoke_handler(tauri::generate_handler![
      desktop_caps,
      save_secret,
      save_secret_tracked,
      load_secret,
      delete_secret,
      list_secrets,
      native_fetch,
      default_library_dir,
      set_library_dir,
      ensure_dir,
      write_text_file,
      read_text_file,
      list_json_files,
    ])
    .setup(|app| {
      // Warm the library folder on first launch so Finder has somewhere obvious.
      let _ = default_library_dir();
      if let Some(win) = app.get_webview_window("main") {
        let _ = win.set_title("Throughline");
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running Throughline desktop");
}
