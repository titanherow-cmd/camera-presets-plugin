package com.camerapresets;

import net.runelite.client.ui.ColorScheme;
import net.runelite.client.ui.PluginPanel;
import net.runelite.client.ui.components.FlatTextField;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

/**
 * Side panel showing 5 camera preset slots.
 * Each slot shows:
 *   - An editable name label
 *   - Saved yaw / pitch / zoom values (or "Empty" if not saved yet)
 *   - Save, Load, and Clear buttons
 */
public class CameraPresetsPanel extends PluginPanel
{
    private static final Color BACKGROUND    = ColorScheme.DARK_GRAY_COLOR;
    private static final Color SLOT_BG       = ColorScheme.DARKER_GRAY_COLOR;
    private static final Color SAVE_COLOR    = new Color(0, 153, 0);
    private static final Color LOAD_COLOR    = new Color(0, 102, 204);
    private static final Color CLEAR_COLOR   = new Color(153, 0, 0);
    private static final Color SAVE_HOVER    = new Color(0, 180, 0);
    private static final Color LOAD_HOVER    = new Color(0, 130, 230);
    private static final Color CLEAR_HOVER   = new Color(200, 0, 0);
    private static final Color EMPTY_TEXT    = ColorScheme.LIGHT_GRAY_COLOR;
    private static final Color SAVED_TEXT    = Color.WHITE;

    private final CameraPresetsPlugin plugin;
    private final CameraPresetsConfig config;

    // Keep references so we can refresh them
    private final JLabel[]        statusLabels = new JLabel[CameraPresetsPlugin.NUM_PRESETS];
    private final FlatTextField[] nameFields   = new FlatTextField[CameraPresetsPlugin.NUM_PRESETS];

    public CameraPresetsPanel(CameraPresetsPlugin plugin, CameraPresetsConfig config)
    {
        super();
        this.plugin = plugin;
        this.config = config;

        setLayout(new BorderLayout());
        setBackground(BACKGROUND);
        setBorder(new EmptyBorder(10, 10, 10, 10));

        // ── Title ────────────────────────────────────────────────────────────
        JLabel title = new JLabel("Camera Presets", SwingConstants.CENTER);
        title.setFont(title.getFont().deriveFont(Font.BOLD, 14f));
        title.setForeground(Color.WHITE);
        title.setBorder(new EmptyBorder(0, 0, 10, 0));
        add(title, BorderLayout.NORTH);

        // ── Preset slots ─────────────────────────────────────────────────────
        JPanel slotsPanel = new JPanel();
        slotsPanel.setLayout(new BoxLayout(slotsPanel, BoxLayout.Y_AXIS));
        slotsPanel.setBackground(BACKGROUND);

        for (int i = 0; i < CameraPresetsPlugin.NUM_PRESETS; i++)
        {
            slotsPanel.add(buildSlotPanel(i + 1));
            slotsPanel.add(Box.createVerticalStrut(8));
        }

        add(slotsPanel, BorderLayout.CENTER);

        // ── Footer hint ───────────────────────────────────────────────────────
        JLabel hint = new JLabel("<html><center>You can also set hotkeys<br>in Plugin Settings</center></html>", SwingConstants.CENTER);
        hint.setForeground(ColorScheme.LIGHT_GRAY_COLOR);
        hint.setFont(hint.getFont().deriveFont(10f));
        hint.setBorder(new EmptyBorder(10, 0, 0, 0));
        add(hint, BorderLayout.SOUTH);
    }

    private JPanel buildSlotPanel(int slot)
    {
        int idx = slot - 1;

        JPanel outer = new JPanel(new BorderLayout());
        outer.setBackground(SLOT_BG);
        outer.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(ColorScheme.BORDER_COLOR, 1),
            new EmptyBorder(8, 8, 8, 8)
        ));
        outer.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));

        // ── Name field ────────────────────────────────────────────────────────
        FlatTextField nameField = new FlatTextField();
        nameField.setText(config.getPresetName(slot));
        nameField.setBackground(SLOT_BG);
        nameField.setHoverBackgroundColor(ColorScheme.DARK_GRAY_HOVER_COLOR);
        nameField.setBorder(new EmptyBorder(0, 0, 4, 0));
        nameField.getTextField().setFont(nameField.getTextField().getFont().deriveFont(Font.BOLD));
        nameField.getTextField().setForeground(Color.WHITE);
        // Save the name whenever the user finishes editing
        nameField.getTextField().addActionListener(e ->
            plugin.renamePreset(slot, nameField.getText().trim()));
        nameField.getTextField().addFocusListener(new java.awt.event.FocusAdapter() {
            @Override public void focusLost(java.awt.event.FocusEvent e) {
                plugin.renamePreset(slot, nameField.getText().trim());
            }
        });
        nameFields[idx] = nameField;
        outer.add(nameField, BorderLayout.NORTH);

        // ── Status label ──────────────────────────────────────────────────────
        JLabel statusLabel = new JLabel();
        statusLabel.setFont(statusLabel.getFont().deriveFont(10f));
        updateStatusLabel(statusLabel, slot);
        statusLabels[idx] = statusLabel;
        outer.add(statusLabel, BorderLayout.CENTER);

        // ── Buttons ───────────────────────────────────────────────────────────
        JPanel buttons = new JPanel(new GridLayout(1, 3, 4, 0));
        buttons.setBackground(SLOT_BG);
        buttons.setBorder(new EmptyBorder(6, 0, 0, 0));

        buttons.add(makeButton("Save",  SAVE_COLOR,  SAVE_HOVER,  () -> plugin.savePreset(slot)));
        buttons.add(makeButton("Load",  LOAD_COLOR,  LOAD_HOVER,  () -> plugin.loadPreset(slot)));
        buttons.add(makeButton("Clear", CLEAR_COLOR, CLEAR_HOVER, () -> {
            int confirm = JOptionPane.showConfirmDialog(
                this,
                "Clear \"" + config.getPresetName(slot) + "\"?",
                "Clear Preset",
                JOptionPane.YES_NO_OPTION
            );
            if (confirm == JOptionPane.YES_OPTION) {
                plugin.clearPreset(slot);
            }
        }));

        outer.add(buttons, BorderLayout.SOUTH);
        return outer;
    }

    /** Refreshes all slot labels and name fields — call after save/clear. */
    public void refreshPresets()
    {
        SwingUtilities.invokeLater(() -> {
            for (int i = 0; i < CameraPresetsPlugin.NUM_PRESETS; i++)
            {
                int slot = i + 1;
                updateStatusLabel(statusLabels[i], slot);
                nameFields[i].setText(config.getPresetName(slot));
            }
        });
    }

    private void updateStatusLabel(JLabel label, int slot)
    {
        int yaw   = config.getPresetYaw(slot);
        int pitch = config.getPresetPitch(slot);
        int zoom  = config.getPresetZoom(slot);

        if (yaw == -1)
        {
            label.setText("<html><i>Empty — click Save to store current view</i></html>");
            label.setForeground(EMPTY_TEXT);
        }
        else
        {
            label.setText(String.format(
                "<html>Yaw: %d &nbsp; Pitch: %d &nbsp; Zoom: %d</html>",
                yaw, pitch, zoom
            ));
            label.setForeground(SAVED_TEXT);
        }
    }

    private JButton makeButton(String text, Color base, Color hover, Runnable action)
    {
        JButton btn = new JButton(text);
        btn.setBackground(base);
        btn.setForeground(Color.WHITE);
        btn.setFocusPainted(false);
        btn.setBorderPainted(false);
        btn.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        btn.setFont(btn.getFont().deriveFont(Font.BOLD, 11f));

        btn.addMouseListener(new MouseAdapter() {
            @Override public void mouseEntered(MouseEvent e) { btn.setBackground(hover); }
            @Override public void mouseExited(MouseEvent e)  { btn.setBackground(base);  }
        });

        btn.addActionListener(e -> action.run());
        return btn;
    }
}
