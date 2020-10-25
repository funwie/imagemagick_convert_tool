
class Image:
    """
    Class to hold metadata about an image
    The metadata is passed around during processing to prevent re-reading the image for it
    The metadata can also be persisted along with the image
    """
    def __init__(self, image_path, format='jpeg'):
        self.image_file_path = image_path
        self.format = format

    def __str__(self):
        return self.image_file_path
