//! Minimal dlltool shim: translates rustc's dlltool invocation into an
//! `lld-link -def:` import-library generation call, so raw-dylib linking
//! works on machines without a full MinGW binutils (no `as.exe`).
//!
//! rustc calls: dlltool -d <def> -D <dllname> -l <out.lib> -m i386:x86-64
//!              -f --64 --no-leading-underscore --temp-prefix <name>
//! We call:     rust-lld -flavor link -def:<def> -out:<out.lib> -machine:x64

use std::io::Write;
use std::path::Path;
use std::process::Command;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();

    let mut def_path: Option<String> = None;
    let mut out_path: Option<String> = None;
    let mut dll_name: Option<String> = None;
    let mut machine = "x64".to_string();

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "-d" | "--input-def" => {
                i += 1;
                def_path = args.get(i).cloned();
            }
            "-D" | "--dllname" => {
                i += 1;
                dll_name = args.get(i).cloned();
            }
            "-l" | "--output-lib" => {
                i += 1;
                out_path = args.get(i).cloned();
            }
            "-m" | "--machine" => {
                i += 1;
                if let Some(m) = args.get(i) {
                    machine = if m.contains("x86-64") || m.contains("amd64") {
                        "x64".to_string()
                    } else if m.contains("i386") || m.contains("x86") {
                        "x86".to_string()
                    } else if m.contains("arm64") || m.contains("aarch64") {
                        "arm64".to_string()
                    } else {
                        machine.clone()
                    };
                }
            }
            // Assembler flags and other dlltool options are not needed for
            // lld-link def-based import library generation.
            _ => {}
        }
        i += 1;
    }

    let def_path = match def_path {
        Some(p) => p,
        None => {
            eprintln!("dlltool-shim: missing -d <input-def>");
            std::process::exit(1);
        }
    };
    let out_path = match out_path {
        Some(p) => p,
        None => {
            eprintln!("dlltool-shim: missing -l <output-lib>");
            std::process::exit(1);
        }
    };

    // lld-link derives the import descriptor DLL name from the LIBRARY line
    // in the def file; rustc passes the dll name via -D, so ensure it exists.
    let mut final_def = def_path.clone();
    if let Some(name) = &dll_name {
        let content = std::fs::read_to_string(&def_path).unwrap_or_default();
        let has_library = content
            .lines()
            .any(|l| l.trim_start().to_ascii_uppercase().starts_with("LIBRARY"));
        if !has_library {
            let patched = format!("LIBRARY {}\n{}", name, content);
            let patched_path = Path::new(&out_path).with_extension("patched.def");
            if let Ok(mut f) = std::fs::File::create(&patched_path) {
                let _ = f.write_all(patched.as_bytes());
                final_def = patched_path.to_string_lossy().to_string();
            }
        }
    }

    let lld = option_env!("OPENZESS_LLD_PATH").unwrap_or("rust-lld");
    let status = Command::new(lld)
        .arg("-flavor")
        .arg("link")
        .arg(format!("-def:{}", final_def))
        .arg(format!("-out:{}", out_path))
        .arg(format!("-machine:{}", machine))
        .status();

    match status {
        Ok(s) if s.success() => std::process::exit(0),
        Ok(s) => {
            eprintln!("dlltool-shim: lld-link failed with {}", s);
            std::process::exit(1);
        }
        Err(e) => {
            eprintln!("dlltool-shim: cannot spawn lld-link ({}): {}", lld, e);
            std::process::exit(1);
        }
    }
}
