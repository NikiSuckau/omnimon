using OmnipetModuleEditor.Models;
using OmnipetModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Windows.Forms;

namespace OmnipetModuleEditor.Controls
{
    /// <summary>
    /// Panel that displays pet sprites and action buttons (Download, Import, Refresh).
    /// Handles sprite display and related actions for a pet.
    /// </summary>
    public class PetSpritePanel : UserControl
    {
        // Sprite display boxes
        private readonly List<PictureBox> spriteBoxes = new List<PictureBox>();

        // Action buttons
        private readonly Button btnDownload;
        private readonly Button btnImport;
        private readonly Button btnRefresh;

        /// <summary>
        /// The current pet whose sprites are being displayed.
        /// </summary>
        public Pet CurrentPet { get; set; }

        /// <summary>
        /// The current module context.
        /// </summary>
        public Module CurrentModule { get; set; }

        /// <summary>
        /// The path to the module directory.
        /// </summary>
        public string ModulePath { get; set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="PetSpritePanel"/> class.
        /// </summary>
        public PetSpritePanel()
        {
            var layout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 9,
                RowCount = 4,
                AutoSize = true
            };

            // Set up columns and rows
            for (int i = 0; i < 9; i++)
                layout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 52F));
            for (int i = 0; i < 4; i++)
                layout.RowStyles.Add(new RowStyle(SizeType.Absolute, i % 2 == 0 ? 48F : 20F));

            string[] spriteLabels = new[]
            {
                "IDLE1", "IDLE2", "HAPPY", "ANGRY",
                "TRAIN1", "TRAIN2", "ATK1", "ATK2",
                "EAT1", "EAT2", "NOPE", "EXTRA",
                "NAP1", "NAP2", "SICK", "LOSE"
            };

            // First row: 8 sprites and labels
            for (int i = 0; i < 8; i++)
            {
                var pb = CreateSpriteBox();
                layout.Controls.Add(pb, i, 0);
                spriteBoxes.Add(pb);

                var lbl = CreateSpriteLabel(spriteLabels[i]);
                layout.Controls.Add(lbl, i, 1);
            }

            // Second row: 7 sprites and labels
            for (int i = 0; i < 7; i++)
            {
                var pb = CreateSpriteBox();
                layout.Controls.Add(pb, i, 2);
                spriteBoxes.Add(pb);

                var lbl = CreateSpriteLabel(spriteLabels[8 + i]);
                layout.Controls.Add(lbl, i, 3);
            }

            // Action buttons
            btnDownload = new Button
            {
                Text = Properties.Resources.Button_Download ?? "Download",
                Width = 48,
                Height = 48,
                Margin = new Padding(2),
                Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
            };
            layout.Controls.Add(btnDownload, 8, 0);

            btnImport = new Button
            {
                Text = Properties.Resources.Button_Import ?? "Import",
                Width = 48,
                Height = 48,
                Margin = new Padding(2),
                Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
            };
            layout.Controls.Add(btnImport, 8, 2);

            btnRefresh = new Button
            {
                Text = Properties.Resources.Button_Refresh ?? "Refresh",
                Width = 48,
                Height = 48,
                Margin = new Padding(2),
                Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
            };
            layout.Controls.Add(btnRefresh, 7, 2);

            this.Controls.Add(layout);

            // Button event handlers
            btnDownload.Click += BtnDownload_Click;
            btnImport.Click += BtnImport_Click;
            btnRefresh.Click += BtnRefresh_Click;
        }

        #region Sprite Display

        /// <summary>
        /// Sets the images for the sprite boxes.
        /// </summary>
        /// <param name="sprites">List of images to display.</param>
        public void SetSprites(List<Image> sprites)
        {
            for (int i = 0; i < spriteBoxes.Count; i++)
            {
                spriteBoxes[i].Image = (sprites != null && i < sprites.Count) ? sprites[i] : null;
            }
        }

        /// <summary>
        /// Loads and displays the sprites for the current pet.
        /// </summary>
        public void RefreshSprites()
        {
            if (CurrentPet != null && CurrentModule != null && !string.IsNullOrEmpty(ModulePath))
            {
                var sprites = PetUtils.LoadPetSprites(ModulePath, CurrentModule, CurrentPet, 15);
                SetSprites(sprites);
            }
            else
            {
                SetSprites(null);
            }
        }

        #endregion

        #region Button Event Handlers

        private void BtnDownload_Click(object sender, EventArgs e)
        {
            if (CurrentPet != null && !string.IsNullOrWhiteSpace(CurrentPet.Name))
            {
                try
                {
                    Clipboard.SetText(CurrentPet.Name);
                }
                catch
                {
                    MessageBox.Show(Properties.Resources.CouldNotCopyName ?? "Could not copy the name to the clipboard.",
                        Properties.Resources.Error ?? "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = "https://dmc-sprite-database.vercel.app/",
                    UseShellExecute = true
                });
            }
            catch
            {
                MessageBox.Show(Properties.Resources.CouldNotOpenBrowser ?? "Could not open the browser.",
                    Properties.Resources.Error ?? "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnImport_Click(object sender, EventArgs e)
        {
            if (CurrentPet == null || CurrentModule == null || string.IsNullOrWhiteSpace(CurrentPet.Name) || string.IsNullOrWhiteSpace(ModulePath))
            {
                MessageBox.Show(Properties.Resources.ImportSpritesSelectPet ?? "Select a valid pet to import sprites.",
                    Properties.Resources.Warning ?? "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // Use fixed name format instead of module.NameFormat
            string zipName = SpriteUtils.GetSpriteName(CurrentPet.Name, SpriteUtils.DefaultNameFormat) + ".zip";

            string downloads = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string downloadsFolder = Path.Combine(downloads, "Downloads");
            string zipPath = Path.Combine(downloadsFolder, zipName);

            if (!File.Exists(zipPath))
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.ImportSpritesFileNotFound ?? "File not found: {0}", zipPath),
                    Properties.Resources.ImportSpritesTitle ?? "Import sprites",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var result = MessageBox.Show(
                string.Format(Properties.Resources.ImportSpritesConfirm ?? "Import sprites from \"{0}\" for this pet?\n\nThe zip file will be copied to the monsters folder.", zipName),
                Properties.Resources.ImportSpritesTitle ?? "Import sprites",
                MessageBoxButtons.YesNo, MessageBoxIcon.Question);

            if (result != DialogResult.Yes)
                return;

            // Determine which monsters folder to use based on high definition setting
            bool useHighDefinition = CurrentModule?.HighDefinitionSprites ?? false;
            string monstersFolder = useHighDefinition ? "monsters_hidef" : "monsters";
            string targetFolder = Path.Combine(ModulePath, monstersFolder);
            
            if (!Directory.Exists(targetFolder))
                Directory.CreateDirectory(targetFolder);

            // Copy the zip file to the appropriate monsters folder
            string destinationZipPath = Path.Combine(targetFolder, zipName);

            try
            {
                File.Copy(zipPath, destinationZipPath, true);

                MessageBox.Show(Properties.Resources.ImportSpritesSuccess ?? "Sprites imported successfully!",
                    Properties.Resources.ImportSpritesTitle ?? "Import sprites", MessageBoxButtons.OK, MessageBoxIcon.Information);

                RefreshSprites();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.ImportSpritesError ?? "Error importing sprites: {0}", ex.Message),
                    Properties.Resources.Error ?? "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnRefresh_Click(object sender, EventArgs e)
        {
            RefreshSprites();
        }

        #endregion

        #region Helpers

        /// <summary>
        /// Creates a PictureBox for displaying a sprite.
        /// </summary>
        private static PictureBox CreateSpriteBox()
        {
            return new PictureBox
            {
                Width = 48,
                Height = 48,
                BackColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle,
                SizeMode = PictureBoxSizeMode.Zoom,
                Margin = new Padding(2)
            };
        }

        /// <summary>
        /// Creates a label for a sprite box.
        /// </summary>
        private static Label CreateSpriteLabel(string text)
        {
            return new Label
            {
                Text = text,
                TextAlign = ContentAlignment.TopCenter,
                Dock = DockStyle.Fill,
                AutoSize = false,
                Width = 48,
                Height = 16,
                Font = new Font(FontFamily.GenericSansSerif, 7, FontStyle.Regular)
            };
        }

        #endregion
    }
}