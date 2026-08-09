<?php

declare(strict_types=1);

namespace Azucar\Services;

/** GD port of image_service.py: downscale to THUMBNAIL_SIZE, save JPEG q80. */
final class ImageService
{
    public static function compressToThumbnail(string $sourcePath, string $targetDir, string $filename): string
    {
        if (!is_dir($targetDir)) {
            mkdir($targetDir, 0775, true);
        }

        $base = pathinfo($filename, PATHINFO_FILENAME);
        $thumbPath = rtrim($targetDir, '/') . "/thumb_{$base}.jpg";

        $info = getimagesize($sourcePath);
        if ($info === false) {
            throw new \RuntimeException('Not a valid image');
        }
        [$width, $height] = $info;

        $image = match ($info[2]) {
            IMAGETYPE_JPEG => imagecreatefromjpeg($sourcePath),
            IMAGETYPE_PNG => imagecreatefrompng($sourcePath),
            IMAGETYPE_WEBP => imagecreatefromwebp($sourcePath),
            IMAGETYPE_GIF => imagecreatefromgif($sourcePath),
            default => throw new \RuntimeException('Unsupported image type'),
        };
        if ($image === false) {
            throw new \RuntimeException('Could not decode image');
        }

        // Phone photos: honor EXIF orientation (Pillow received pre-oriented
        // frames; GD does not)
        if ($info[2] === IMAGETYPE_JPEG && function_exists('exif_read_data')) {
            $exif = @exif_read_data($sourcePath);
            $orientation = (int) ($exif['Orientation'] ?? 1);
            if ($orientation === 3) {
                $image = imagerotate($image, 180, 0);
            } elseif ($orientation === 6) {
                $image = imagerotate($image, -90, 0);
                [$width, $height] = [$height, $width];
            } elseif ($orientation === 8) {
                $image = imagerotate($image, 90, 0);
                [$width, $height] = [$height, $width];
            }
        }

        $maxSize = (int) ($_ENV['THUMBNAIL_SIZE'] ?? 400);
        $scale = min(1.0, $maxSize / max($width, $height));
        $newWidth = max(1, (int) round($width * $scale));
        $newHeight = max(1, (int) round($height * $scale));

        $thumb = imagecreatetruecolor($newWidth, $newHeight);
        // White background for transparent PNG/WebP (JPEG has no alpha)
        $white = imagecolorallocate($thumb, 255, 255, 255);
        imagefill($thumb, 0, 0, $white);
        imagecopyresampled($thumb, $image, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);

        if (!imagejpeg($thumb, $thumbPath, 80)) {
            throw new \RuntimeException('Could not save thumbnail');
        }
        imagedestroy($image);
        imagedestroy($thumb);

        return $thumbPath;
    }

    public static function uploadsDir(): string
    {
        $dir = $_ENV['UPLOADS_DIR'] ?? '';
        if ($dir === '') {
            $dir = dirname(__DIR__, 2) . '/public/uploads';
        }
        return rtrim($dir, '/');
    }
}
