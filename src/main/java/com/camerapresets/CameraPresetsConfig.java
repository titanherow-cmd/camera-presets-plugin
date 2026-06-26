package com.camerapresets;

import net.runelite.client.config.Config;
import net.runelite.client.config.ConfigGroup;
import net.runelite.client.config.ConfigItem;
import net.runelite.client.config.ConfigSection;
import net.runelite.client.config.Keybind;

@ConfigGroup("camerapresets")
public interface CameraPresetsConfig extends Config
{
    // -------------------------------------------------------------------------
    // Sections
    // -------------------------------------------------------------------------

    @ConfigSection(name = "Preset 1 Hotkeys", description = "Hotkeys for preset slot 1", position = 0)
    String section1 = "section1";

    @ConfigSection(name = "Preset 2 Hotkeys", description = "Hotkeys for preset slot 2", position = 1)
    String section2 = "section2";

    @ConfigSection(name = "Preset 3 Hotkeys", description = "Hotkeys for preset slot 3", position = 2)
    String section3 = "section3";

    @ConfigSection(name = "Preset 4 Hotkeys", description = "Hotkeys for preset slot 4", position = 3)
    String section4 = "section4";

    @ConfigSection(name = "Preset 5 Hotkeys", description = "Hotkeys for preset slot 5", position = 4)
    String section5 = "section5";

    // -------------------------------------------------------------------------
    // Hotkeys — one Save + one Load per slot
    // -------------------------------------------------------------------------

    @ConfigItem(keyName = "saveHotkey1", name = "Save Preset 1", description = "Hold to save current camera as preset 1", section = "section1", position = 0)
    default Keybind saveHotkey1() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "loadHotkey1", name = "Load Preset 1", description = "Press to restore preset 1", section = "section1", position = 1)
    default Keybind loadHotkey1() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "saveHotkey2", name = "Save Preset 2", description = "Hold to save current camera as preset 2", section = "section2", position = 0)
    default Keybind saveHotkey2() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "loadHotkey2", name = "Load Preset 2", description = "Press to restore preset 2", section = "section2", position = 1)
    default Keybind loadHotkey2() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "saveHotkey3", name = "Save Preset 3", description = "Hold to save current camera as preset 3", section = "section3", position = 0)
    default Keybind saveHotkey3() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "loadHotkey3", name = "Load Preset 3", description = "Press to restore preset 3", section = "section3", position = 1)
    default Keybind loadHotkey3() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "saveHotkey4", name = "Save Preset 4", description = "Hold to save current camera as preset 4", section = "section4", position = 0)
    default Keybind saveHotkey4() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "loadHotkey4", name = "Load Preset 4", description = "Press to restore preset 4", section = "section4", position = 1)
    default Keybind loadHotkey4() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "saveHotkey5", name = "Save Preset 5", description = "Hold to save current camera as preset 5", section = "section5", position = 0)
    default Keybind saveHotkey5() { return Keybind.NOT_SET; }

    @ConfigItem(keyName = "loadHotkey5", name = "Load Preset 5", description = "Press to restore preset 5", section = "section5", position = 1)
    default Keybind loadHotkey5() { return Keybind.NOT_SET; }

    // -------------------------------------------------------------------------
    // Stored preset data — hidden from the config UI, managed by the plugin
    // -1 means "slot is empty / not yet saved"
    // -------------------------------------------------------------------------

    @ConfigItem(keyName = "preset1Name",  name = "", description = "", hidden = true) default String preset1Name()  { return "Preset 1"; }
    @ConfigItem(keyName = "preset1Yaw",   name = "", description = "", hidden = true) default int    preset1Yaw()   { return -1; }
    @ConfigItem(keyName = "preset1Pitch", name = "", description = "", hidden = true) default int    preset1Pitch() { return -1; }
    @ConfigItem(keyName = "preset1Zoom",  name = "", description = "", hidden = true) default int    preset1Zoom()  { return -1; }

    @ConfigItem(keyName = "preset2Name",  name = "", description = "", hidden = true) default String preset2Name()  { return "Preset 2"; }
    @ConfigItem(keyName = "preset2Yaw",   name = "", description = "", hidden = true) default int    preset2Yaw()   { return -1; }
    @ConfigItem(keyName = "preset2Pitch", name = "", description = "", hidden = true) default int    preset2Pitch() { return -1; }
    @ConfigItem(keyName = "preset2Zoom",  name = "", description = "", hidden = true) default int    preset2Zoom()  { return -1; }

    @ConfigItem(keyName = "preset3Name",  name = "", description = "", hidden = true) default String preset3Name()  { return "Preset 3"; }
    @ConfigItem(keyName = "preset3Yaw",   name = "", description = "", hidden = true) default int    preset3Yaw()   { return -1; }
    @ConfigItem(keyName = "preset3Pitch", name = "", description = "", hidden = true) default int    preset3Pitch() { return -1; }
    @ConfigItem(keyName = "preset3Zoom",  name = "", description = "", hidden = true) default int    preset3Zoom()  { return -1; }

    @ConfigItem(keyName = "preset4Name",  name = "", description = "", hidden = true) default String preset4Name()  { return "Preset 4"; }
    @ConfigItem(keyName = "preset4Yaw",   name = "", description = "", hidden = true) default int    preset4Yaw()   { return -1; }
    @ConfigItem(keyName = "preset4Pitch", name = "", description = "", hidden = true) default int    preset4Pitch() { return -1; }
    @ConfigItem(keyName = "preset4Zoom",  name = "", description = "", hidden = true) default int    preset4Zoom()  { return -1; }

    @ConfigItem(keyName = "preset5Name",  name = "", description = "", hidden = true) default String preset5Name()  { return "Preset 5"; }
    @ConfigItem(keyName = "preset5Yaw",   name = "", description = "", hidden = true) default int    preset5Yaw()   { return -1; }
    @ConfigItem(keyName = "preset5Pitch", name = "", description = "", hidden = true) default int    preset5Pitch() { return -1; }
    @ConfigItem(keyName = "preset5Zoom",  name = "", description = "", hidden = true) default int    preset5Zoom()  { return -1; }

    // -------------------------------------------------------------------------
    // Helper methods — retrieve data for a given slot number (1-5)
    // -------------------------------------------------------------------------

    default Keybind getSaveHotkey(int slot)
    {
        switch (slot) {
            case 1: return saveHotkey1();
            case 2: return saveHotkey2();
            case 3: return saveHotkey3();
            case 4: return saveHotkey4();
            case 5: return saveHotkey5();
            default: return Keybind.NOT_SET;
        }
    }

    default Keybind getLoadHotkey(int slot)
    {
        switch (slot) {
            case 1: return loadHotkey1();
            case 2: return loadHotkey2();
            case 3: return loadHotkey3();
            case 4: return loadHotkey4();
            case 5: return loadHotkey5();
            default: return Keybind.NOT_SET;
        }
    }

    default String getPresetName(int slot)
    {
        switch (slot) {
            case 1: return preset1Name();
            case 2: return preset2Name();
            case 3: return preset3Name();
            case 4: return preset4Name();
            case 5: return preset5Name();
            default: return "Preset " + slot;
        }
    }

    default int getPresetYaw(int slot)
    {
        switch (slot) {
            case 1: return preset1Yaw();
            case 2: return preset2Yaw();
            case 3: return preset3Yaw();
            case 4: return preset4Yaw();
            case 5: return preset5Yaw();
            default: return -1;
        }
    }

    default int getPresetPitch(int slot)
    {
        switch (slot) {
            case 1: return preset1Pitch();
            case 2: return preset2Pitch();
            case 3: return preset3Pitch();
            case 4: return preset4Pitch();
            case 5: return preset5Pitch();
            default: return -1;
        }
    }

    default int getPresetZoom(int slot)
    {
        switch (slot) {
            case 1: return preset1Zoom();
            case 2: return preset2Zoom();
            case 3: return preset3Zoom();
            case 4: return preset4Zoom();
            case 5: return preset5Zoom();
            default: return -1;
        }
    }
}
