
import subprocess


def avi2mp4(filepath_avi: str):
    """
    Convert an avi file to a mp4 file.
    """
    filepath_mp4 = filepath_avi.replace('.avi', '.mp4')
    bash_command = f"ffmpeg -i {filepath_avi} -vcodec libx264 -crf 25 -pix_fmt yuv420p -y {filepath_mp4}"
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    process.communicate()
    return filepath_mp4