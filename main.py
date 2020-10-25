from pathlib import Path
import json
import asyncio
import sys

SAME_OUTPUT_SIZE = '100%'
DEFAULT_OUTPUT_FORMAT = 'jpeg'


async def run(cmd):
    """
    Async command runner
    :param cmd: The command to run
    :return:
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    log(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        log(f'[stdout]\n{stdout.decode()}')
    if stderr:
        log(f'[stderr]\n{stderr.decode()}')


def log(msg):
    # Simple logger example
    print(msg)


def file_exist_and_is_valid(file_path: str) -> bool:
    """
    Check if the given file path is valid and file exist
    Changes could be made to file after this check, and before we use the file
    But it's still better to at least check and not queue a covert job for file that doesn't exist or wrong file
    :param file_path: file to
    :return: True is valid file, else False
    """
    if not file_path:
        return False

    # We expect only jpeg or jpg image files for now
    if not file_path.lower().endswith(('.jpg', '.jpeg')):
        return False

    file = Path(file_path)
    if file.is_file():
        return True
    return False


def load_json_data(json_file_path: str):
    """
    Read image conversion tasks from json file
    :param json_file_path:
    :return: list of image conversions
    """
    log(f'Loading data from {json_file_path}')
    try:
        with open(json_file_path) as json_file:
            data = json.load(json_file)
            log(f'Loaded data from {json_file_path}')
            return data
    except FileNotFoundError as not_found_error:
        log({not_found_error})
    except PermissionError as file_permission_error:
        log({file_permission_error})
    except (OSError, IOError, Exception) as error:
        log({error})
    log(f'Failed to load data from {json_file_path}. Existing')
    exit() # Exist because we can't proceed without data


def get_filename_with_extension(filename: str, file_format: str = 'jpeg'):
    # TO DO - Validation of allowed file formats required
    if not file_format:
        file_format = DEFAULT_OUTPUT_FORMAT
    return f'{filename}.{file_format.lower()}'


def get_image_size(size: str) -> str:
    if not size:
        return SAME_OUTPUT_SIZE

    if size[-1] != '%':
        size = f'{size}%'

    percent_value = size[:-1]
    try:
        percent_number = int(percent_value)
        if percent_number > 100:
            return SAME_OUTPUT_SIZE
        else:
            return size
    except ValueError as error:
        return SAME_OUTPUT_SIZE


def convert_image(input_image_file, output_size, output_image_filename):
    cmd_args = [input_image_file]
    if output_size != SAME_OUTPUT_SIZE:
        cmd_args += ['-resize', output_size]
    cmd = ['magick', 'convert'] + cmd_args + [output_image_filename]

    try:
        log(f'Running Command: {cmd}')
        str_cmd = ' '.join(cmd)
        asyncio.run(run(str_cmd))
    except (asyncio.TimeoutError, asyncio.CancelledError, Exception) as error:
        log(f'Failed to convert {input_image_file} to {output_image_filename}')
        log(f'Command Error {error}')


def process_single_image(image_conversion_data):
    """
    Process a single image conversion task
    :param image_conversion_data: dict of conversion values
    :return:
    """
    input_image_file = image_conversion_data['inputImageFile']
    output_image_size = get_image_size(image_conversion_data['outputImageSize'])
    output_image_filename = get_filename_with_extension(image_conversion_data['outputImageFileName'],
                                                        image_conversion_data['outputImageFormat'])

    log(f'Converting {input_image_file} to {output_image_filename} at scale {output_image_size}')
    convert_image(input_image_file, output_image_size, output_image_filename)
    log(f'{input_image_file} Converted to {output_image_filename} at scale {output_image_size}')


def process_images_from_json_file(json_filename: str):
    """
    Read image conversions from a json file and process them
    :param json_filename: json file with list of image conversions
    :return:
    """
    # we can not proceed without data
    if not json_filename:
        return

    images_data = load_json_data(json_filename)

    # These images can now be queued as jobs
    # Conversion Workers will pick up the jobs and do the conversion
    # We can add more Conversion Workers as demand increases
    # For this simple solution, i will just iterate and process all the task
    conversion_count = 0
    log(f'Converting {len(images_data)} images')
    for image_data in images_data:
        input_image_file = image_data['inputImageFile']
        if file_exist_and_is_valid(input_image_file):
            process_single_image(image_data)
            conversion_count += 1
        else:
            log(f'File {input_image_file} not valid or does not exist')

    failed_conversions = len(images_data) - conversion_count
    log(f'Image conversion completed. {conversion_count} images converted. {failed_conversions} images failed')


if __name__ == '__main__':
    # Single image
    single_image_data = {
        "inputImageFile": "logo.jpeg",
        "outputImageSize": "100%",
        "outputImageFileName": "single_more",
        "outputImageFormat": "png"
    }
    process_single_image(single_image_data)

    if len(sys.argv) > 1:
        data_file = sys.argv[1]

        # Images from a json file - see data.json for schema
        process_images_from_json_file(data_file)
    else:
        log('Data argument file is missing')
        exit()


