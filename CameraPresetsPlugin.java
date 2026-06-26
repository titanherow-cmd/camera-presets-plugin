package com.camerapresets;

import com.google.inject.Provides;
import javax.inject.Inject;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import net.runelite.api.Client;
import net.runelite.client.config.ConfigManager;
import net.runelite.client.input.KeyManager;
import net.runelite.client.plugins.Plugin;
import net.runelite.client.plugins.PluginDescriptor;
import net.runelite.client.ui.ClientToolbar;
import net.runelite.client.ui.NavigationButton;
import net.runelite.client.util.HotkeyListener;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@PluginDescriptor(
    name = "Camera Presets",
    description = "Save and restore camera angle, pitch, and zoom presets",
    tags = {"camera", "zoom", "angle", "preset", "pitch", "yaw"}
)
public class CameraPresetsPlugin extends Plugin
{
    static final int NUM_PRESETS = 5;

    @Inject private Client client;
    @Inject private CameraPresetsConfig config;
    @Inject private ConfigManager configManager;
    @Inject private KeyManager keyManager;
    @Inject private ClientToolbar clientToolbar;

    private CameraPresetsPanel panel;
    private NavigationButton navButton;

    private final HotkeyListener[] saveListeners = new HotkeyListener[NUM_PRESETS];
    private final HotkeyListener[] loadListeners = new HotkeyListener[NUM_PRESETS];

    @Override
    protected void startUp() throws Exception
    {
        panel = new CameraPresetsPanel(this, config);

        // Draw a simple "C" icon programmatically — no file needed
        BufferedImage icon = new BufferedImage(16, 16, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = icon.createGraphics();
        g.setColor(new Color(200, 150, 0));
        g.fillOval(1, 1, 14, 14);
        g.setColor(Color.BLACK);
        g.drawString("C", 4, 12);
        g.dispose();

        navButton = NavigationButton.builder()
            .tooltip("Camera Presets")
            .icon(icon)
            .priority(10)
            .panel(panel)
            .build();
        clientToolbar.addNavigation(navButton);

        for (int i = 0; i < NUM_PRESETS; i++)
        {
            final int slot = i;
            saveListeners[i] = new HotkeyListener(() -> config.getSaveHotkey(slot + 1))
            {
                @Override public void hotkeyPressed() { savePreset(slot + 1); }
            };
            loadListeners[i] = new HotkeyListener(() -> config.getLoadHotkey(slot + 1))
            {
                @Override public void hotkeyPressed() { loadPreset(slot + 1); }
            };
            keyManager.registerKeyListener(saveListeners[i]);
            keyManager.registerKeyListener(loadListeners[i]);
        }
        log.info("Camera Presets started");
    }

    @Override
    protected void shutDown() throws Exception
    {
        clientToolbar.removeNavigation(navButton);
        for (int i = 0; i < NUM_PRESETS; i++)
        {
            keyManager.unregisterKeyListener(saveListeners[i]);
            keyManager.unregisterKeyListener(loadListeners[i]);
        }
        log.info("Camera Presets stopped");
    }

    public void savePreset(int slot)
    {
        int yaw   = client.getCameraYaw();
        int pitch = client.getCameraPitch();
        int zoom  = client.getScale();

        configManager.setConfiguration("camerapresets", "preset" + slot + "Yaw",   yaw);
        configManager.setConfiguration("camerapresets", "preset" + slot + "Pitch", pitch);
        configManager.setConfiguration("camerapresets", "preset" + slot + "Zoom",  zoom);

        log.debug("Saved preset {}: yaw={}, pitch={}, zoom={}", slot, yaw, pitch, zoom);
        if (panel != null) panel.refreshPresets();
    }

    public void loadPreset(int slot)
    {
        int yaw   = config.getPresetYaw(slot);
        int pitch = config.getPresetPitch(slot);
        int zoom  = config.getPresetZoom(slot);

        if (yaw == -1)
        {
            log.debug("Preset {} is empty", slot);
            return;
        }

        client.setCameraYawTarget(yaw);
        client.setCameraPitchTarget(pitch);
        // Set zoom via the game's built-in zoom var
        client.setVarcIntValue(168, zoom);

        log.debug("Loaded preset {}: yaw={}, pitch={}, zoom={}", slot, yaw, pitch, zoom);
    }

    public void clearPreset(int slot)
    {
        configManager.setConfiguration("camerapresets", "preset" + slot + "Yaw",   -1);
        configManager.setConfiguration("camerapresets", "preset" + slot + "Pitch", -1);
        configManager.setConfiguration("camerapresets", "preset" + slot + "Zoom",  -1);
        configManager.setConfiguration("camerapresets", "preset" + slot + "Name",  "Preset " + slot);
        if (panel != null) panel.refreshPresets();
    }

    public void renamePreset(int slot, String name)
    {
        configManager.setConfiguration("camerapresets", "preset" + slot + "Name", name);
    }

    @Provides
    CameraPresetsConfig provideConfig(ConfigManager configManager)
    {
        return configManager.getConfig(CameraPresetsConfig.class);
    }
}
