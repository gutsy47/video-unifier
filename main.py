from moviepy.editor import *
from pathlib import Path
from random import choice
from proglog import TqdmProgressBarLogger
from colorama import init, Back, Style
from timeit import default_timer
import configparser


def get_folder_files(path):
    return [str(file) for file in Path(path).iterdir()]


def get_out_filename(path):
    if not get_folder_files(path):
        return f"{path}\\1.mp4"
    result = str(sorted(int(x.split('\\')[-1][:-4]) for x in get_folder_files(path))[-1] + 1)
    return f"{path}\\{result}.mp4"


def get_list_of_images(folder):
    result = []
    folder = Path(folder)
    if folder.is_file():
        img = ImageClip(str(folder), duration=1)
        result.append(img)
    if folder.is_dir():
        for file in sorted(folder.iterdir(), reverse=True):
            img = ImageClip(str(file), duration=1)
            result.append(img)
    return result


if __name__ == '__main__':

    # Colorama init
    init()

    # Open & read the config
    config = configparser.ConfigParser()
    config.read("config.ini", encoding='utf-8')

    in_files = get_folder_files(config["path"]["input"])
    images = get_list_of_images(config["path"]["image"])
    sounds = get_folder_files(config["path"]["audio"])

    crop_start, crop_end = int(config["crop"]["start"]), int(config["crop"]["end"])
    fadein_duration = int(config["fadein"]["duration"])
    image_duration, image_size = int(config["image"]["duration"]), float(config["image"]["size"])
    unq_filter_params = config["filter"]["unq_params"].split('\n')[1:]

    # Estimated time based on previous runs
    with open(r"total_time.txt", 'r', encoding='utf-8') as f:
        time, files = map(float, f.read().split('\n'))
        estimated_per_file = round(time / files, 1)
        estimated = estimated_per_file * len(in_files)

    # Print info
    estimated_print = f"{int(estimated / 60)}m {round(estimated % 60)}s"
    print(
        "Paths:\n\t"
        f" INPUT | {config['path']['input']}\n\t"
        f"OUTPUT | {config['path']['output']}\n\t"
        f"IMAGES | {config['path']['image']}\n\t"
        f"AUDIOS | {config['path']['audio']}\n"
        "\nSettings:\n\t"
        f"  CROP | {crop_start}:{crop_end}\n\t"
        f"FADEIN | {fadein_duration}\n\t"
        f" IMAGE | {image_duration} {image_size}\n\t"
        "\nUnique filters:\n",
        *[f" {param[:param.find('=')]} | {param[param.find('=')+1:]}\n" for param in unq_filter_params],
        Back.YELLOW + f"\nEstimated time: {estimated_print} ({estimated_per_file}s per file)" + Style.RESET_ALL,
        "\n"
    )

    # Main loop
    timer_start = default_timer()
    for index, filename in enumerate(get_folder_files(config["path"]["input"])):

        # Just logs
        print(Back.YELLOW + "Processing:" + Style.RESET_ALL, filename)

        # Proceed the video
        clip: VideoFileClip = VideoFileClip(filename, audio=False)  # Get the clip
        clip = clip.subclip(crop_start, crop_end)  # Crop
        clip = vfx.fadein(clip, duration=fadein_duration)  # Fade in
        clip = vfx.mirror_x(clip)  # Vertical flip

        # Add noise
        audio: AudioFileClip = AudioFileClip(choice(sounds)).subclip(crop_start, crop_end)  # Get audio and crop
        clip = clip.set_audio(audio)

        # Compose clip with image
        image = choice(images).set_duration(image_duration).resize(image_size)
        clip: CompositeVideoClip = CompositeVideoClip(
            [clip, image.set_position(("center", 0.68), relative=True).set_start(clip.duration - 5)]
        )

        # Save the clip
        outfile = get_out_filename(config["path"]["output"])
        clip.write_videofile(
            filename=outfile,
            codec='libx264',
            audio_codec='aac',
            ffmpeg_params=['-filter_complex', choice(unq_filter_params)],
            logger=TqdmProgressBarLogger(print_messages=False)
        )

        # Just logs
        progress = f"{index+1} of {len(in_files)} | {round((index+1)/len(in_files)*100)}%"
        print(Back.GREEN + " Completed:" + Style.RESET_ALL, outfile, Back.GREEN + progress + Style.RESET_ALL)

    # Log out
    elapsed = round(default_timer() - timer_start, 1)
    print(f"\n     Estimated time: {estimated}s")
    print(f"Actual elapsed time: {elapsed}s")
    out = input("\nEnter anything to exit...")
    with open(r"total_time.txt", 'w', encoding='utf-8') as f:
        time += elapsed
        files += len(in_files)
        f.write(f"{time}\n{files}")
