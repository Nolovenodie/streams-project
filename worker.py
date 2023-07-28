import os
import re
import sys
import glob
import shutil
import datetime
from app import app, logger
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
from ffmpeg_streaming._utiles import cnv_options_to_args, mkdir
from ffmpeg_streaming._process import Process
from utils import md5


@app.task(bind=True)
def handle_movie(self, path, outpath):
    try:
        # 开始下载视频
        self.update_state(state="PROGRESS", meta={"msg": "准备下载视频"})
        download_path = os.path.join("cache", md5(os.path.basename(path.replace("'", ""))))

        def download_monitor(task_id, per, eta):
            handle_movie.update_state(task_id=task_id, state="PROGRESS", meta={"msg": "下载视频中", "eta": eta, "per": str(round(per * 100, 2)) + "%"})
        rclone_command("copy", path, download_path, download_monitor, self.request.id)

        # 开始处理视频
        self.update_state(state="PROGRESS", meta={"msg": "准备转码视频"})

        # 寻找最大文件判定为视频
        files = glob.glob(os.path.join(download_path, "*"))
        if not files:
            raise Exception("视频文件不存在")
        video_file = max(files, key=os.path.getsize)

        # 创建输出目录
        handle_path = download_path + "_output"
        mkdir(handle_path)

        # 处理视频
        def convert_monitor(task_id, per, eta):
            handle_movie.update_state(task_id=task_id, state="PROGRESS", meta={"msg": "处理视频中", "eta": eta, "per": str(round(per * 100, 2)) + "%"})
        convert_video(video_file, handle_path, convert_monitor, self.request.id)

        # 处理预览视频
        self.update_state(state="PROGRESS", meta={"msg": "准备生成 Preview"})
        preview_generate(handle_path, handle_path)

        # 处理预览表
        self.update_state(state="PROGRESS", meta={"msg": "准备生成 Thumbs"})

        def thumbs_monitor(task_id, per, eta):
            handle_movie.update_state(task_id=task_id, state="PROGRESS", meta={"msg": "处理预览表中", "eta": eta, "per": str(round(per * 100, 2)) + "%"})
        thumbs_generate(video_file, handle_path, monitor=thumbs_monitor, task_id=self.request.id)

        # 元数据转移
        fault = move_metadata(download_path, handle_path)
        shutil.rmtree(download_path)

        # 上传结果
        def upload_monitor(task_id, per, eta):
            handle_movie.update_state(task_id=task_id, state="PROGRESS", meta={"msg": "上传视频中", "eta": eta, "per": str(round(per * 100, 2)) + "%"})
        rclone_command("move", handle_path, outpath, upload_monitor, self.request.id)
        shutil.rmtree(handle_path)

        return {"msg": "处理完毕", "fault": fault}

    except Exception as e:
        error_message = str(e)
        self.update_state(state='FAILURE', meta={"msg": error_message})
        raise


def rclone_command(command, path, outpath, monitor: callable = None, task_id=None):
    command = ["rclone", command, path, outpath, "-P"]
    command = " ".join(command).replace("\\", "/")

    def _monitor(task_id, line):
        per_match = re.findall(r"(\d+)%", line)
        eta_match = re.search(r"ETA (.*)s", line)

        if per_match and eta_match:
            per = per_match[-1]
            eta = eta_match.group(1)

            if callable(monitor):
                try:
                    monitor(task_id, int(per) / 100, eta + "s")
                except Exception as e:
                    logger.error(str(e))

    with Process(object(), command, _monitor, task_id) as process:
        process.run()


def move_metadata(path, outpath):
    fault = []
    # nfo
    try:
        poster = glob.glob(path + "/*.nfo")[0]
        shutil.move(poster, os.path.join(outpath, "metadata.nfo"))
    except:
        return fault.append("不存在 Nfo")
    # poster
    try:
        poster = glob.glob(path + "/*poster.*")[0]
        shutil.move(poster, os.path.join(outpath, "poster.jpg"))
    except:
        return fault.append("不存在 Poster")
    # cover
    try:
        covers = glob.glob(path + "/*thumb.*")
        if len(covers) == 0:
            covers = glob.glob(path + "/*fanart.*")
        cover = covers[0]
        shutil.move(cover, os.path.join(outpath, "cover.jpg"))
    except:
        return fault.append("不存在 Cover")
    return " ".join(fault)


def convert_video(video_file, outpath, monitor, task_id):
    def _monitor(task_id, line, duration, time_, time_left, process):
        try:
            monitor(task_id, time_ / duration, str(datetime.timedelta(seconds=int(time_left))))
        except Exception as e:
            logger.error(str(e))

    video = ffmpeg_streaming.input(video_file)

    _1080p = Representation(Size(1920, 1080), Bitrate(3000 * 1024, 128 * 1024))
    _720p = Representation(Size(1280, 720), Bitrate(1500 * 1024, 128 * 1024))
    _480p = Representation(Size(854, 480), Bitrate(500 * 1024, 128 * 1024))

    hls = video.hls(Formats.h264("h264_nvenc"))
    hls.representations(_1080p, _720p, _480p)
    hls.output(outpath, monitor=_monitor, task_id=task_id)


def preview_generate(path, outpath, count=15):
    outfile = os.path.join(outpath, "preview.mp4")
    dirname = os.path.join(path, "streams", "480p")
    streams = glob.glob(os.path.join(dirname, "*.ts"))
    length = len(streams) / (count + 1)

    if os.path.exists(outfile):
        os.remove(outfile)

    streams = [os.path.join(dirname, str(int((i + 1) * length)) + ".ts") for i in range(count)]
    count = len(streams)

    command = ["ffmpeg"] + ["-i " + ts for ts in streams]
    command += cnv_options_to_args({
        "filter_complex": f'"{"".join([f"[{i}:v]trim=duration=1,scale=320:-1[outv{i}];" for i in range(count)])} {"".join([f"[outv{i}]" for i in range(count)])}concat=n={count}:v=1:a=0"',
        "c:v": "libx264",
        "an": outfile
    })
    command = " ".join(command).replace("\\", "/")

    with Process(None, command) as process:
        process.run()


def thumbs_generate(video_file, outpath, second=3, width=300, monitor: callable = None, task_id=None):
    def _monitor(task_id, line, duration, time_, time_left, process):
        try:
            monitor(task_id, time_ / duration, str(datetime.timedelta(seconds=int(time_left))))
        except Exception as e:
            logger.error(str(e))

    # 视频抽帧
    frames_path = os.path.join(outpath, "frames")
    mkdir(frames_path)

    command = ["ffmpeg", "-i", f"'{video_file}'", "-y"]
    command += cnv_options_to_args({
        "vf": f"fps=1/{second},scale={width}:-1",
        "progress": "pipe:1"
    })
    command += [os.path.join(frames_path, "%8d.png")]
    command = " ".join(command).replace("\\", "/")

    with Process(None, command, _monitor, task_id) as process:
        process.run()

    # 合成精灵表
    command = ["thumbs" if sys.platform == "win32" else os.path.join(".", "thumbs"), "'" + frames_path + "'"]
    command += cnv_options_to_args({
        "o": outpath,
        "w": width,
        "s": second
    })
    command = " ".join(command).replace("\\", "/")

    with Process(None, command) as process:
        process.run()
