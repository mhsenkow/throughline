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
use std::sync::{Mutex, OnceLock};
use tauri::ipc::Channel;
use tauri::Manager;

const SERVICE: &str = "org.throughline.desktop";

// ── Model downloads ────────────────────────────────────────────────────────
//
// The reason this app has a desktop build at all, applied to weights. A browser
// cannot stream twenty gigabytes to a folder you own, resume it after a dropped
// connection, or leave it there for another program to use. This can.
//
// Nothing here runs a model. It fetches files and gets out of the way — the
// engine that reads them (Forge, SD.Next, Draw Things, ComfyUI) is a separate
// program the user already trusts, reached over localhost. Embedding an
// inference runtime would mean shipping GPU kernels we cannot test on every
// machine, and would make this app the thing that breaks when a model format
// changes.

/// Cancelled downloads, by destination file name. A multi-gigabyte transfer you
/// cannot stop is a bug, not a feature.
fn cancels() -> &'static Mutex<std::collections::HashSet<String>> {
  static C: OnceLock<Mutex<std::collections::HashSet<String>>> = OnceLock::new();
  C.get_or_init(|| Mutex::new(std::collections::HashSet::new()))
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct DownloadProgress {
  kind: String, // "start" | "progress" | "done" | "cancelled" | "error"
  received: u64,
  total: Option<u64>,
  path: Option<String>,
  error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
struct ModelFile {
  file: String,
  bytes: u64,
  partial: bool,
}

/// Reject anything that could climb out of the models folder. The catalogue is
/// ours, but the file name reaches Rust from JS and is therefore untrusted.
fn safe_file_name(name: &str) -> Result<String, String> {
  let n = name.trim();
  if n.is_empty()
    || n.contains('/')
    || n.contains('\\')
    || n.contains('\0')
    || n.starts_with('.')
    || n.len() > 200
  {
    return Err(format!("{name:?} is not a usable file name"));
  }
  Ok(n.to_string())
}

fn models_root() -> Result<PathBuf, String> {
  let dir = resolve_library_root()?.join("models");
  fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
  Ok(dir)
}

/// The transfer itself, kept free of Tauri types so it can be tested without a
/// running app — see the tests at the bottom of this file.
async fn stream_to_disk(
  url: &str,
  dest: &Path,
  mut on: impl FnMut(u64, Option<u64>),
  cancelled: impl Fn() -> bool,
) -> Result<u64, String> {
  let part = dest.with_extension("part");
  let already = fs::metadata(&part).map(|m| m.len()).unwrap_or(0);

  let client = reqwest::Client::builder()
    .user_agent(format!("Throughline-Desktop/{}", env!("CARGO_PKG_VERSION")))
    .build()
    .map_err(|e| e.to_string())?;
  let mut req = client.get(url);
  if already > 0 {
    req = req.header(reqwest::header::RANGE, format!("bytes={already}-"));
  }
  let res = req.send().await.map_err(|e| e.to_string())?;
  let status = res.status();
  if !status.is_success() {
    return Err(format!("HTTP {} fetching {url}", status.as_u16()));
  }

  // 206 means the server honoured the range and we append. Anything else means
  // it ignored it — start again rather than corrupting the file with a second
  // copy of the head, which is the classic resume bug.
  let resuming = status.as_u16() == 206 && already > 0;
  let mut received = if resuming { already } else { 0 };
  let total = res
    .content_length()
    .map(|len| len + if resuming { already } else { 0 });

  let file = fs::OpenOptions::new()
    .create(true)
    .write(true)
    .append(resuming)
    .truncate(!resuming)
    .open(&part)
    .map_err(|e| e.to_string())?;
  let mut out = std::io::BufWriter::with_capacity(1 << 20, file);

  on(received, total);
  let mut last_ping = std::time::Instant::now();
  let mut stream = res.bytes_stream();
  while let Some(chunk) = stream.next().await {
    if cancelled() {
      out.flush().ok();
      return Err("cancelled".into());
    }
    let bytes = chunk.map_err(|e| e.to_string())?;
    out.write_all(&bytes).map_err(|e| e.to_string())?;
    received += bytes.len() as u64;
    // Ten updates a second is plenty; a progress event per 8 KB chunk would
    // spend more time in the IPC channel than on the network.
    if last_ping.elapsed().as_millis() >= 100 {
      last_ping = std::time::Instant::now();
      on(received, total);
    }
  }
  out.flush().map_err(|e| e.to_string())?;
  drop(out);

  if let Some(total) = total {
    if received != total {
      return Err(format!(
        "transfer ended early — {received} of {total} bytes. The part file is kept, so downloading again resumes."
      ));
    }
  }
  fs::rename(&part, dest).map_err(|e| e.to_string())?;
  on(received, total);
  Ok(received)
}

#[tauri::command]
async fn download_model(
  url: String,
  file: String,
  on_progress: Channel<DownloadProgress>,
) -> Result<String, String> {
  let name = safe_file_name(&file)?;
  let dest = models_root()?.join(&name);
  cancels().lock().map_err(|e| e.to_string())?.remove(&name);

  let _ = on_progress.send(DownloadProgress {
    kind: "start".into(), received: 0, total: None,
    path: Some(dest.to_string_lossy().to_string()), error: None,
  });

  let ping = on_progress.clone();
  let watch = name.clone();
  let result = stream_to_disk(
    &url,
    &dest,
    |received, total| {
      let _ = ping.send(DownloadProgress {
        kind: "progress".into(), received, total, path: None, error: None,
      });
    },
    || {
      cancels()
        .lock()
        .map(|c| c.contains(&watch))
        .unwrap_or(false)
    },
  )
  .await;

  match result {
    Ok(received) => {
      let _ = on_progress.send(DownloadProgress {
        kind: "done".into(), received, total: Some(received),
        path: Some(dest.to_string_lossy().to_string()), error: None,
      });
      Ok(dest.to_string_lossy().to_string())
    }
    Err(e) if e == "cancelled" => {
      let _ = on_progress.send(DownloadProgress {
        kind: "cancelled".into(), received: 0, total: None, path: None, error: None,
      });
      Err("cancelled".into())
    }
    Err(e) => {
      let _ = on_progress.send(DownloadProgress {
        kind: "error".into(), received: 0, total: None, path: None,
        error: Some(e.clone()),
      });
      Err(e)
    }
  }
}

#[tauri::command]
fn cancel_download(file: String) -> Result<(), String> {
  let name = safe_file_name(&file)?;
  cancels().lock().map_err(|e| e.to_string())?.insert(name);
  Ok(())
}

#[tauri::command]
fn list_models() -> Result<Vec<ModelFile>, String> {
  let dir = models_root()?;
  let mut out = Vec::new();
  for entry in fs::read_dir(&dir).map_err(|e| e.to_string())?.flatten() {
    let meta = match entry.metadata() {
      Ok(m) if m.is_file() => m,
      _ => continue,
    };
    let file = entry.file_name().to_string_lossy().to_string();
    let partial = file.ends_with(".part");
    out.push(ModelFile { file, bytes: meta.len(), partial });
  }
  out.sort_by(|a, b| a.file.cmp(&b.file));
  Ok(out)
}

#[tauri::command]
fn delete_model(file: String) -> Result<(), String> {
  let name = safe_file_name(&file)?;
  let path = models_root()?.join(&name);
  if path.exists() {
    fs::remove_file(&path).map_err(|e| e.to_string())?;
  }
  Ok(())
}

#[tauri::command]
fn models_dir() -> Result<String, String> {
  Ok(models_root()?.to_string_lossy().to_string())
}

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
  fs::create_dir_all(dir.join("models")).map_err(|e| e.to_string())?;
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
      download_model,
      cancel_download,
      list_models,
      delete_model,
      models_dir,
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

#[cfg(test)]
mod tests {
  use super::*;

  #[test]
  fn file_names_cannot_escape_the_models_folder() {
    assert!(safe_file_name("flux1-schnell-Q4_K_S.gguf").is_ok());
    for bad in ["../secrets", "a/b", "..", ".hidden", "", "  "] {
      assert!(safe_file_name(bad).is_err(), "{bad:?} should be rejected");
    }
  }

  /// Exercises the real transfer against a local server, including the resume
  /// path — truncate a half-finished .part file and check the second attempt
  /// appends to it instead of starting over or doubling the head.
  ///
  ///   cd desktop/src-tauri && cargo test -- --ignored
  ///
  /// Ignored by default because it needs `python3 -m http.server 8719` running
  /// in the repo root; a test that fails on a laptop with no server is a test
  /// people learn to skip.
  #[tokio::test]
  #[ignore]
  async fn downloads_and_resumes() {
    let url = "http://localhost:8719/library.json";
    let dir = std::env::temp_dir().join("throughline-dl-test");
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    let dest = dir.join("library.json");

    let whole = stream_to_disk(url, &dest, |_, _| {}, || false).await.unwrap();
    assert!(whole > 1000, "expected a real file, got {whole} bytes");
    let full = fs::read(&dest).unwrap();

    // Half a file, left behind as if the connection dropped.
    fs::remove_file(&dest).unwrap();
    let part = dest.with_extension("part");
    fs::write(&part, &full[..(full.len() / 2)]).unwrap();

    let resumed = stream_to_disk(url, &dest, |_, _| {}, || false).await.unwrap();
    assert_eq!(resumed, whole, "resumed transfer should report the whole size");
    assert_eq!(fs::read(&dest).unwrap(), full, "resumed file must be byte-identical");

    let _ = fs::remove_dir_all(&dir);
  }
}
