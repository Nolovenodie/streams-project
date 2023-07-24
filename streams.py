import os
import sys
import datetime
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size

if len(sys.argv) != 2:
    exit("请传入视频路径")
video_file = sys.argv[1]


def monitor(ffmpeg, duration, time_, time_left, process):
    per = round(time_ / duration * 100)
    sys.stdout.write(
        "\r视频转码切片 |%s%s| %s%% [%s]" %
        ('█' * per, ' ' * (100 - per), per, datetime.timedelta(seconds=int(time_left)))
    )
    sys.stdout.flush()


# video = ffmpeg_streaming.input(os.path.join("test", "300MAAN-637.mp4"))
video = ffmpeg_streaming.input(video_file)

_1080p = Representation(Size(1920, 1080), Bitrate(3000 * 1024, 128 * 1024))
_720p = Representation(Size(1280, 720), Bitrate(1500 * 1024, 128 * 1024))
_480p = Representation(Size(854, 480), Bitrate(500 * 1024, 128 * 1024))

hls = video.hls(Formats.h264("h264_nvenc"))
hls.representations(_1080p, _720p, _480p)
hls.output(monitor=monitor)

sys.stdout.flush()
print("\r\n视频处理完毕")
