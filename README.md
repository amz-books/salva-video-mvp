# MVP de download de vídeos

Aplicação local para pré-visualizar um link do YouTube e baixar um vídeo em MP4 quando você tem autorização para salvá-lo.

## Executar

1. No Windows, dê dois cliques em `iniciar.cmd` (ou execute `.\iniciar.ps1` no PowerShell).
2. Abra `http://localhost:8000`.

O script usa o Python disponível neste computador e instala a dependência na pasta do projeto caso ela esteja ausente. Em outro computador, instale Python 3.10 ou superior antes de executar.

O download usa `yt-dlp`, Node.js e FFmpeg para combinar vídeo e áudio em MP4. Você pode escolher qualidade baixa (até 360p), média (até 480p) ou boa (até 720p). Se o vídeo não tiver exatamente a resolução escolhida, o programa usa a melhor resolução disponível abaixo do limite. O script instala `yt-dlp` e FFmpeg na pasta do projeto; instale Node.js se ele não estiver disponível. Alguns vídeos podem exigir atualização das ferramentas, ter restrições ou não disponibilizar um formato MP4 compatível. O serviço aceita apenas links `youtube.com` e `youtu.be`, não processa playlists e limita os vídeos a 1 hora. Use somente em vídeos que você pode baixar. Os termos do YouTube restringem downloads fora das formas permitidas pelo serviço, por autorização ou por lei aplicável.

Este MVP é local. Antes de disponibilizar publicamente, revise as permissões de uso, a infraestrutura e os limites de acesso.
