# Overview

ParentText chatbots need supporting media files. This project contains a script that will transcode source audio/video files to those that meet the ParentText specification.

## Requirements

- Install the [FFmpeg] command
- Obtain source audio/video files

## CLI

```
python -m parenttext.transcode --help
```

## Examples

Transcode video files from the 'src' directory and save them as video files in the 'dst' directory.
```
python -m parenttext.transcode src dst
```

Transcode audio and video files from the 'src' directory and save them as audio-only files in the 'dst' directory.
```
python -m parenttext.transcode -f audio src dst
```


[FFmpeg]: https://ffmpeg.org/
