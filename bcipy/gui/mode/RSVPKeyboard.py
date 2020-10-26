# pylint: disable=no-member
"""GUI for running RSVP tasks"""
import datetime
import itertools
import os
import subprocess

import wx

from bcipy.gui.gui_main import BCIGui
from bcipy.helpers.load import load_json_parameters, copy_parameters
from bcipy.helpers.load import DEFAULT_PARAMETERS_PATH

from bcipy.tasks.task_registry import ExperimentType

class RSVPKeyboard(BCIGui):
    """GUI for launching the RSVP tasks."""

    def __init__(self, *args, **kwargs):
        super(RSVPKeyboard, self).__init__(*args, **kwargs)
        self.event_started = False
        self.parameter_location = DEFAULT_PARAMETERS_PATH

    def bind_action(self, action: str, btn) -> None:
        if action == 'launch_bci':
            self.Bind(wx.EVT_BUTTON, self.launch_bci_main, btn)
        elif action == 'edit_parameters':
            self.Bind(wx.EVT_BUTTON, self.edit_parameters, btn)
        elif action == 'select_parameters':
            self.Bind(wx.EVT_BUTTON, self.select_parameters, btn)
        elif action == 'refresh':
            self.Bind(wx.EVT_BUTTON, self.refresh, btn)
        elif action == 'offline_analysis':
            self.Bind(wx.EVT_BUTTON, self.offline_analysis, btn)
        elif action == 'load_items_from_txt':
            self.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.load_items_from_txt, btn)
        else:
            self.Bind(wx.EVT_BUTTON, self.on_clicked, btn)

    def select_parameters(self, _event) -> None:
        """Dialog to select the parameters.json configuration to use."""
        with wx.FileDialog(self,
                           'Select parameters file',
                           wildcard='JSON files (*.json)|*.json',
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() != wx.ID_CANCEL:
                self.parameter_location = fd.GetPath()

    def edit_parameters(self, _event) -> None:
        """Edit Parameters. Prompts for a parameters.json file to use. If the default parameters
        are selected a copy is used.
        """
        if self.parameter_location == DEFAULT_PARAMETERS_PATH:
            # Don't allow the user to overwrite the defaults
            with wx.MessageDialog(
                    self,
                    "The default parameters.json can't be overridden. A copy will be used.",
                    'Info', wx.OK | wx.CANCEL) as confirm_dialog:
                response = confirm_dialog.ShowModal()
                if response == wx.ID_OK:
                    self.parameter_location = copy_parameters()
                else:
                    return

        subprocess.call(
            f'python bcipy/gui/params_form.py -p {self.parameter_location}',
            shell=True)

    def launch_bci_main(self, event: wx.Event) -> None:
        """Launch BCI MAIN"""
        if self.check_input():
            self.event_started = True
            username = self.comboboxes[0].GetValue().replace(" ", "_")
            experiment_type = event.GetEventObject().GetId()
            mode = 'RSVP'
            # TODO: add -p flag and use configured parameter_location
            cmd = 'python bci_main.py -m {} -t {} -u {} -p {}'.format(
                mode, experiment_type, username, self.parameter_location)

            subprocess.Popen(cmd, shell=True)

    def check_input(self) -> bool:
        """Check Input."""
        try:
            if self.comboboxes[0].GetValue() == '':
                dialog = wx.MessageDialog(
                    self, "Please Input User ID", 'Info',
                    wx.OK | wx.ICON_WARNING)
                dialog.ShowModal()
                dialog.Destroy()
                return False
            if self.event_started:
                return False
        except Exception as e:
            dialog = wx.MessageDialog(
                self, f'Error, {e}',
                'Info', wx.OK | wx.ICON_WARNING)
            dialog.ShowModal()
            dialog.Destroy()
            return False
        return True

    def offline_analysis(self, _event: wx.Event) -> None:
        """Run the offline analysis in a new Process."""
        cmd = 'python bcipy/signal/model/offline_analysis.py'
        self.event_started = True
        subprocess.Popen(cmd, shell=True)

    def refresh(self, _event: wx.Event) -> None:
        self.event_started = False

    def load_items_from_txt(self, _event):
        """Loads user directory names from the data path defined in
        parameters.json, and adds those directory names as items to the user id
        selection combobox."""
        parameters = load_json_parameters(
            self.parameter_location, value_cast=True)
        data_save_loc = parameters['data_save_loc']
        if os.path.isdir(data_save_loc):
            saved_users = os.listdir(data_save_loc)
        elif os.path.isdir('bcipy/' + data_save_loc):
            saved_users = os.listdir('bcipy/' + data_save_loc)
        else:
            raise IOError('User data save location not found')
        self.comboboxes[0].Clear()
        self.comboboxes[0].AppendItems(saved_users)


def run_rsvp_gui():
    """Create the GUI and run"""
    tasks = ExperimentType.by_mode()['RSVP']

    task_colors = itertools.cycle(
        [wx.Colour(221, 37, 56), wx.Colour(239, 146, 40),
         wx.Colour(239, 212, 105), wx.Colour(117, 173, 48),
         wx.Colour(62, 161, 232), wx.Colour(192, 122, 224),
         wx.Colour(5, 62, 221)])

    side_padding = 15
    btn_width_apart = 105
    btn_padding = 20

    window_width = (len(tasks) * btn_width_apart) + btn_padding
    # Start the app and init the main GUI
    app = wx.App(False)
    gui = RSVPKeyboard(
        title="RSVPKeyboard", size=(window_width, 550), background_color='black')

    # STATIC TEXT!
    gui.add_static_text(
        text='RSVPKeyboard', position=(185, 0), size=25, color='white')
    gui.add_static_text(
        text='1.) Enter a User ID:', position=(75, 110), size=15, color='white')
    gui.add_static_text(
        text='2.) Choose your experiment type:',
        position=(75, 250), size=15, color='white')

    # BUTTONS!
    btn_size = (85, 80)
    btn_pos_x = side_padding
    btn_pos_y = 300
    for task in tasks:
        gui.add_button(
            message=task.label,
            position=(btn_pos_x, btn_pos_y),
            size=btn_size,
            color=next(task_colors),
            action='launch_bci',
            id=task.value)
        btn_pos_x += btn_width_apart

    command_btn_height = 40
    gui.add_button(
        message='Load Parameters', position=(side_padding, 450),
        size=(105, command_btn_height), color='white',
        action='select_parameters')
    gui.add_button(
        message='Edit', position=(side_padding + 110, 450),
        size=(50, command_btn_height), color='white',
        action='edit_parameters')

    btn_auc_width = 100
    btn_auc_x = window_width - (2 * side_padding + btn_auc_width)
    gui.add_button(
        message='Calculate AUC', position=(btn_auc_x, 450),
        size=(btn_auc_width, command_btn_height), color='white',
        action='offline_analysis')

    btn_refresh_width = 50
    btn_refresh_x = window_width - (2 * side_padding + btn_refresh_width)
    gui.add_button(
        message='Refresh', position=(btn_refresh_x, 230),
        size=(btn_refresh_width, command_btn_height), color='white',
        action='refresh')

    # TEXT INPUT
    gui.add_combobox(position=(75, 150), size=(
        250, 25), action='load_items_from_txt')

    # IMAGES
    gui.add_image(
        path='bcipy/static/images/gui_images/ohsu.png', position=(side_padding, 0), size=100)
    gui.add_image(
        path='bcipy/static/images/gui_images/neu.png', position=(530, 0), size=100)

    # Make the GUI Show now
    gui.show_gui()
    app.MainLoop()


if __name__ == "__main__":
    run_rsvp_gui()
