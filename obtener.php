<?php
// ID del video de Dailymotion
$video_id = 'x9eh45w'; // Cambia esto por el ID del video que desees
$video_url = "https://www.dailymotion.com/video/$video_id";

// Comando para obtener la URL del video MP4 usando yt-dlp
$command = "yt-dlp -g $video_url";

// Ejecutar el comando
$video_mp4_url = shell_exec($command);

// Verificar si se obtuvo la URL del video
if (!empty($video_mp4_url)) {
    echo "URL de descarga MP4: " . trim($video_mp4_url);
} else {
    echo 'No se pudo obtener la URL del video.';
}
?>
