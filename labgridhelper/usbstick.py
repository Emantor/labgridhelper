#!/usr/bin/env python
import enum

from labgrid.protocol import CommandProtocol, FileTransferProtocol


class USBStatus(enum.Enum):
    """This class describes the USBStick Status"""
    unplugged = 0
    plugged = 1
    mounted = 2


class USBStick:
    """The USBStick class provides an easy to use interface to describe a
    target as an USB Stick."""

    def __init__(self, command, filetransfer, image_dir):
        assert isinstance(command, CommandProtocol)
        assert isinstance(filetransfer, FileTransferProtocol)
        self.command = command
        self.fileservice = filetransfer
        self.status = USBStatus.unplugged
        self._images = []
        self.image_dir = image_dir

    def plug_in(self):
        """Insert the USBStick

        This function plugs the virtual USB Stick in, making it available to
        the connected computer."""
        if not self.image_name:
            raise StateError("No Image selected, please upload and select an image")
        if self.status == USBStatus.unplugged:
            self.command.run_check(
                "modprobe g_mass_storage file={dir}{image}".format(
                    dir=self.image_dir, image=self.image_name
                )
            )
            self.status = USBStatus.plugged

    def plug_out(self):
        """Plugs out the USBStick

        Plugs out the USBStick from the connected computer, does nothing if it is
        already unplugged"""
        if self.status == USBStatus.plugged:
            self.command.run_check("modprobe -r g_mass_storage")
            self.status = USBStatus.unplugged

    def put_file(self, filename, destination=""):
        """Put a file onto the USBStick Image

        Puts a file onto the USB Stick, raises a StateError if it is not
        mounted on the host computer."""
        if not destination:
            destination = os.path.basename(filename)
        if self.status != USBStatus.unplugged:
            raise StateError("Device still plugged in, can't upload image")
        self.command.run_check(
            "losetup -Pf {}/{}".format(self.image_dir, self.image_name)
        )
        self.command.run_check("mount /dev/loop0p1 /mnt/")
        self.fileservice.put(
            filename,
            "/mnt/{dest}".format(
                dest=destination
            )
        )
        self.command.run_check("umount /mnt/")
        self.command.run_check("losetup -D")

    def get_file(self, filename):
        """Gets a file from the USBStick Image

        Gets a file from the USB Stick, raises a StateError if it is not
        mounted on the host computer."""
        if self.status != USBStatus.unplugged:
            raise StateError("Device still plugged in, can't upload image")
        self.command.run_check(
            "losetup -Pf {}/{}".format(self.image_dir, self.image_name)
        )
        self.command.run_check("mount /dev/loop0p1 /mnt/")
        self.fileservice.get(
            "/mnt/{filename}".format(
                filename=filename
            )
        )
        self.command.run_check("umount /mnt/")
        self.command.run_check("losetup -D")

    def upload_image(self, image):
        """Upload a complete image as a new USB Stick

        This replaces the current USB Stick image, storing it permanently on
        the RiotBoard."""
        if self.status != USBStatus.unplugged:
            raise StateError("Device still plugged in, can't insert new image")
        self.fileservice.put(image, self.image_dir)
        self._images.append(os.path.basename(image))

    def switch_image(self, image_name):
        """Switch between already uploaded images on the target."""
        if self.status != USBStatus.unplugged:
            raise StateError("Device still plugged in, can't switch to different image")
        if image_name not in self._images:
            raise StateError("No such Image available")
        self.command.run("umount /mnt/")
        self.command.run("losetup -D")
        self.image_name = image_name


class StateError(Exception):
    """Exception which indicates a error in the state handling of the test"""
    pass
