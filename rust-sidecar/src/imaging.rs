//! Pixel conversion + JPEG/PNG encoding for the sidecar.

use image::codecs::jpeg::JpegEncoder;
use image::codecs::png::PngEncoder;
use image::{DynamicImage, ImageBuffer, Rgb};
use std::io::Cursor;

/// Encode a raw pixel buffer into JPEG or PNG bytes.
pub fn encode(
    raw: &[u8],
    width: u32,
    height: u32,
    layout: &str,
    format: &str,
    quality: u8,
) -> Result<(Vec<u8>, &'static str), String> {
    let (w, h) = (width as usize, height as usize);
    let bytes_per_px = match layout {
        "rgb" => 3,
        "rgba" | "bgra" | "bgrx" => 4,
        other => return Err(format!("unsupported x-layout: {other}")),
    };
    let expected = w.checked_mul(h).and_then(|n| n.checked_mul(bytes_per_px));
    let expected = match expected {
        Some(n) => n,
        None => return Err("dimensions overflow".into()),
    };
    if raw.len() < expected {
        return Err(format!(
            "payload too small: got {} bytes, need {} for {width}x{height} ({layout})",
            raw.len(),
            expected
        ));
    }

    let rgb: Vec<u8> = match layout {
        "rgb" => raw[..expected].to_vec(),
        "rgba" => raw[..expected]
            .chunks_exact(4)
            .flat_map(|px| [px[0], px[1], px[2]])
            .collect(),
        _ => raw[..expected]
            .chunks_exact(4)
            .flat_map(|px| [px[2], px[1], px[0]])
            .collect(),
    };

    let img = ImageBuffer::<Rgb<u8>, Vec<u8>>::from_raw(width, height, rgb)
        .ok_or_else(|| "buffer conversion failed".to_string())?;
    let dyn_img = DynamicImage::ImageRgb8(img);

    match format {
        "jpeg" | "jpg" => {
            let mut cursor = Cursor::new(Vec::with_capacity(expected / 4));
            let encoder = JpegEncoder::new_with_quality(&mut cursor, quality);
            dyn_img
                .write_with_encoder(encoder)
                .map_err(|e| format!("jpeg encode failed: {e}"))?;
            Ok((cursor.into_inner(), "image/jpeg"))
        }
        "png" => {
            let mut cursor = Cursor::new(Vec::with_capacity(expected / 2));
            let encoder = PngEncoder::new(&mut cursor);
            dyn_img
                .write_with_encoder(encoder)
                .map_err(|e| format!("png encode failed: {e}"))?;
            Ok((cursor.into_inner(), "image/png"))
        }
        other => Err(format!("unsupported x-format: {other}")),
    }
}
