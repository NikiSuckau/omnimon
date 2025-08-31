using OmnimonModuleEditor.Models;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnimonModuleEditor.Tabs
{
    /// <summary>
    /// Editor tab for managing items in the module.
    /// </summary>
    public partial class ItemTab : UserControl
    {
        // Fields
        private ListBox lstItems;
        private Button btnAdd;
        private Button btnRemove;
        private Button btnSave;
        private Button btnCancel;

        private TextBox txtName;
        private TextBox txtDescription;
        private ComboBox cmbSpriteName;
        private ComboBox cmbEffect;
        private ComboBox cmbStatus;
        private NumericUpDown numAmount;
        private NumericUpDown numBoostTime;
        private NumericUpDown numWeightGain;
        private PictureBox pbSprite;

        private ComboBox cmbComponentItem;

        private List<Item> items = new List<Item>();
        private string modulePath;
        private Module module;
        private Item selectedItem;

        /// <summary>
        /// Initializes a new instance of the <see cref="ItemTab"/> class.
        /// </summary>
        public ItemTab()
        {
            InitializeComponent();
            this.Name = "ItemTab";
        }

        /// <summary>
        /// Sets the module context for this tab.
        /// </summary>
        public void SetModule(string modulePath, Module module)
        {
            this.modulePath = modulePath;
            this.module = module;
            EnsureItemsFolderAndPopulateSprites();
            PopulateEffectCombo();
            PopulateStatusCombo();
            LoadItemsFromJson();
            PopulateItemList();
        }

        #region Layout and UI Initialization

        /// <summary>
        /// Initializes the layout and UI controls.
        /// </summary>
        private void InitializeComponent()
        {
            this.Dock = DockStyle.Fill;

            var mainLayout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 1,
                Padding = new Padding(8),
                BackColor = SystemColors.Control
            };
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 260));
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));

            // Left panel: List and buttons
            var leftPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 2,
                ColumnCount = 1,
                BackColor = SystemColors.ControlLight
            };
            leftPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
            leftPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));

            lstItems = new ListBox
            {
                Dock = DockStyle.Fill,
                Font = new Font(FontFamily.GenericSansSerif, 10, FontStyle.Regular)
            };
            lstItems.SelectedIndexChanged += LstItems_SelectedIndexChanged;
            leftPanel.Controls.Add(lstItems, 0, 0);

            var buttonPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                Padding = new Padding(4),
                AutoSize = false,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                WrapContents = false
            };
            btnAdd = new Button { Text = "Add", Width = 70, Margin = new Padding(0, 0, 4, 0) };
            btnRemove = new Button { Text = "Remove", Width = 70, Margin = new Padding(0, 0, 4, 0) };
            btnAdd.Click += BtnAdd_Click;
            btnRemove.Click += BtnRemove_Click;
            buttonPanel.Controls.Add(btnAdd);
            buttonPanel.Controls.Add(btnRemove);
            leftPanel.Controls.Add(buttonPanel, 0, 1);

            mainLayout.Controls.Add(leftPanel, 0, 0);

            // Right panel: Item fields
            var rightPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 10, // Increased from 9 to 10 for WeightGain field
                Padding = new Padding(16, 8, 8, 8),
                AutoSize = true
            };
            rightPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100F));
            rightPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100F));

            int row = 0;

            rightPanel.Controls.Add(new Label { Text = "Name:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            txtName = new TextBox { Dock = DockStyle.Fill };
            rightPanel.Controls.Add(txtName, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Description:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            txtDescription = new TextBox { Dock = DockStyle.Fill, Multiline = true, Height = 48, ScrollBars = ScrollBars.Vertical };
            rightPanel.Controls.Add(txtDescription, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Sprite Name:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            cmbSpriteName = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
            cmbSpriteName.SelectedIndexChanged += (s, e) => LoadSprite();
            rightPanel.Controls.Add(cmbSpriteName, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Effect:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            cmbEffect = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
            rightPanel.Controls.Add(cmbEffect, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Component Item:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            cmbComponentItem = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList, Enabled = false };
            rightPanel.Controls.Add(cmbComponentItem, 1, row++);
            cmbComponentItem.Items.Add("");

            rightPanel.Controls.Add(new Label { Text = "Status:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            cmbStatus = new ComboBox { Dock = DockStyle.Fill, DropDownStyle = ComboBoxStyle.DropDownList };
            rightPanel.Controls.Add(cmbStatus, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Amount:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            numAmount = new NumericUpDown { Dock = DockStyle.Left, Minimum = 1, Maximum = 9999, Width = 80, Value = 1 };
            rightPanel.Controls.Add(numAmount, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Boost Time:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            numBoostTime = new NumericUpDown { Dock = DockStyle.Left, Minimum = 0, Maximum = 9999, Width = 80, Value = 0 };
            rightPanel.Controls.Add(numBoostTime, 1, row++);

            rightPanel.Controls.Add(new Label { Text = "Weight Gain:", TextAlign = ContentAlignment.MiddleRight, Dock = DockStyle.Fill }, 0, row);
            numWeightGain = new NumericUpDown { Dock = DockStyle.Left, Minimum = 0, Maximum = 99, Width = 80, Value = 0 };
            rightPanel.Controls.Add(numWeightGain, 1, row++);

            // Sprite box
            pbSprite = new PictureBox
            {
                Width = 48,
                Height = 48,
                SizeMode = PictureBoxSizeMode.Zoom,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.White,
                Margin = new Padding(4)
            };
            var spritePanel = new Panel
            {
                Height = 56,
                Dock = DockStyle.Top
            };
            spritePanel.Controls.Add(pbSprite);
            rightPanel.Controls.Add(new Label(), 0, row); // empty label for alignment
            rightPanel.Controls.Add(spritePanel, 1, row++);

            // Save and Cancel buttons
            btnSave = new Button { Text = "Save", Width = 80, Margin = new Padding(8, 8, 8, 8) };
            btnCancel = new Button { Text = "Cancel", Width = 80, Margin = new Padding(8, 8, 8, 8) };
            var buttonPanelRight = new FlowLayoutPanel
            {
                Dock = DockStyle.Top,
                FlowDirection = FlowDirection.LeftToRight,
                AutoSize = true
            };
            buttonPanelRight.Controls.Add(btnSave);
            buttonPanelRight.Controls.Add(btnCancel);
            rightPanel.Controls.Add(new Label(), 0, row); // empty label for alignment
            rightPanel.Controls.Add(buttonPanelRight, 1, row++);

            mainLayout.Controls.Add(rightPanel, 1, 0);

            this.Controls.Add(mainLayout);

            btnSave.Click += BtnSave_Click;
            btnCancel.Click += BtnCancel_Click;
            cmbEffect.SelectedIndexChanged += (s, e) => UpdateComponentItemCombo();
        }

        #endregion

        #region Data Loading and Population

        /// <summary>
        /// Ensures the items folder exists and populates the sprite combo box.
        /// </summary>
        private void EnsureItemsFolderAndPopulateSprites()
        {
            if (string.IsNullOrEmpty(modulePath))
                return;

            string itemsFolder = Path.Combine(modulePath, "items");
            if (!Directory.Exists(itemsFolder))
                Directory.CreateDirectory(itemsFolder);

            cmbSpriteName.Items.Clear();
            var spriteFiles = Directory.GetFiles(itemsFolder, "*.png")
                .Select(f => Path.GetFileNameWithoutExtension(f))
                .OrderBy(f => f)
                .ToArray();

            cmbSpriteName.Items.AddRange(spriteFiles);
        }

        /// <summary>
        /// Populates the effect combo box.
        /// </summary>
        private void PopulateEffectCombo()
        {
            cmbEffect.Items.Clear();
            cmbEffect.Items.Add(""); // Option for "None" or empty
            foreach (var value in Enum.GetValues(typeof(EffectEnum)))
                cmbEffect.Items.Add(value.ToString());
        }

        /// <summary>
        /// Populates the status combo box.
        /// </summary>
        private void PopulateStatusCombo()
        {
            cmbStatus.Items.Clear();
            cmbStatus.Items.Add(""); // Option for "None" or empty
            foreach (var value in Enum.GetValues(typeof(StatusEnum)))
                cmbStatus.Items.Add(value.ToString());
        }

        /// <summary>
        /// Loads items from the item.json file.
        /// </summary>
        private void LoadItemsFromJson()
        {
            items.Clear();
            lstItems.Items.Clear();
            if (string.IsNullOrEmpty(modulePath))
                return;

            string itemPath = Path.Combine(modulePath, "item.json");
            if (File.Exists(itemPath))
            {
                try
                {
                    string json = File.ReadAllText(itemPath);
                    using (JsonDocument doc = JsonDocument.Parse(json))
                    {
                        var root = doc.RootElement;
                        if (root.TryGetProperty("item", out var itemsElement))
                        {
                            items = JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText());
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error loading item.json: " + ex.Message);
                }
            }
        }

        /// <summary>
        /// Populates the item list box with item names.
        /// </summary>
        private void PopulateItemList()
        {
            lstItems.Items.Clear();
            if (items == null) return;
            foreach (var item in items)
            {
                lstItems.Items.Add(item.Name);
            }
        }

        #endregion

        #region Item Selection and Editing

        /// <summary>
        /// Handles item selection change in the list.
        /// </summary>
        private void LstItems_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (lstItems.SelectedIndex < 0 || lstItems.SelectedIndex >= items.Count)
            {
                selectedItem = null;
                ClearFields();
                return;
            }
            selectedItem = items[lstItems.SelectedIndex];
            LoadFieldsFromItem(selectedItem);
        }

        /// <summary>
        /// Loads the selected item's fields into the UI.
        /// </summary>
        private void LoadFieldsFromItem(Item item)
        {
            txtName.Text = item.Name ?? "";
            txtDescription.Text = item.Description ?? "";
            cmbSpriteName.SelectedItem = item.SpriteName ?? "";
            cmbEffect.SelectedItem = string.IsNullOrEmpty(item.Effect) ? "" : item.Effect;
            cmbStatus.SelectedItem = string.IsNullOrEmpty(item.Status) ? "" : item.Status;
            numAmount.Value = Math.Max(numAmount.Minimum, Math.Min(numAmount.Maximum, item.Amount));
            numBoostTime.Value = Math.Max(numBoostTime.Minimum, Math.Min(numBoostTime.Maximum, item.BoostTime));
            numWeightGain.Value = Math.Max(numWeightGain.Minimum, Math.Min(numWeightGain.Maximum, item.WeightGain));
            UpdateComponentItemCombo();
            cmbComponentItem.SelectedItem = string.IsNullOrEmpty(item.ComponentItem) ? "" : item.ComponentItem;
            LoadSprite();
        }

        /// <summary>
        /// Clears all item fields in the UI.
        /// </summary>
        private void ClearFields()
        {
            txtName.Text = "";
            txtDescription.Text = "";
            cmbSpriteName.SelectedIndex = -1;
            cmbEffect.SelectedIndex = 0;
            cmbStatus.SelectedIndex = 0;
            numAmount.Value = 1;
            numBoostTime.Value = 0;
            numWeightGain.Value = 0;
            pbSprite.Image = null;
            cmbComponentItem.SelectedIndex = 0;
        }

        /// <summary>
        /// Loads the sprite image for the selected sprite name.
        /// </summary>
        private void LoadSprite()
        {
            pbSprite.Image = null;
            if (string.IsNullOrEmpty(modulePath) || cmbSpriteName.SelectedItem == null)
                return;
            string spriteName = cmbSpriteName.SelectedItem.ToString();
            if (string.IsNullOrWhiteSpace(spriteName))
                return;
            string spritePath = Path.Combine(modulePath, "items", spriteName + ".png");
            if (File.Exists(spritePath))
            {
                try
                {
                    using (var fs = new FileStream(spritePath, FileMode.Open, FileAccess.Read, FileShare.Read))
                    {
                        var img = Image.FromStream(fs);
                        pbSprite.Image = new Bitmap(img);
                    }
                }
                catch
                {
                    pbSprite.Image = null;
                }
            }
        }

        #endregion

        #region Button Events

        /// <summary>
        /// Handles the Add button click event.
        /// </summary>
        private void BtnAdd_Click(object sender, EventArgs e)
        {
            var newItem = new Item
            {
                Name = "New Item",
                Description = "",
                SpriteName = "",
                Effect = "",
                Status = "",
                Amount = 1,
                BoostTime = 0,
                WeightGain = 0,
                Id = ""
            };
            items.Add(newItem);
            PopulateItemList();
            lstItems.SelectedIndex = items.Count - 1;
        }

        /// <summary>
        /// Handles the Remove button click event.
        /// </summary>
        private void BtnRemove_Click(object sender, EventArgs e)
        {
            if (lstItems.SelectedIndex < 0 || lstItems.SelectedIndex >= items.Count)
                return;
            var result = MessageBox.Show(
                $"Do you want to remove the item \"{items[lstItems.SelectedIndex].Name}\"?",
                "Confirmation",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning
            );
            if (result == DialogResult.Yes)
            {
                items.RemoveAt(lstItems.SelectedIndex);
                PopulateItemList();
                ClearFields();
            }
        }

        /// <summary>
        /// Handles the Save button click event.
        /// </summary>
        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (selectedItem == null || lstItems.SelectedIndex < 0)
                return;

            selectedItem.Name = txtName.Text;
            selectedItem.Description = txtDescription.Text;
            selectedItem.SpriteName = cmbSpriteName.SelectedItem?.ToString() ?? "";
            selectedItem.Effect = cmbEffect.SelectedItem?.ToString() ?? "";
            selectedItem.Status = cmbStatus.SelectedItem?.ToString() ?? "";
            selectedItem.Amount = (int)numAmount.Value;
            selectedItem.BoostTime = (int)numBoostTime.Value;
            selectedItem.WeightGain = (int)numWeightGain.Value;
            selectedItem.ComponentItem = cmbComponentItem.SelectedItem?.ToString() ?? "";

            lstItems.Items[lstItems.SelectedIndex] = selectedItem.Name;
        }

        /// <summary>
        /// Handles the Cancel button click event.
        /// </summary>
        private void BtnCancel_Click(object sender, EventArgs e)
        {
            if (selectedItem != null)
                LoadFieldsFromItem(selectedItem);
        }

        #endregion

        #region Save to File

        /// <summary>
        /// Saves the current item list to item.json.
        /// </summary>
        public void Save()
        {
            if (string.IsNullOrEmpty(modulePath) || items == null)
                return;

            // Update selected item with current fields
            if (selectedItem != null && lstItems.SelectedIndex >= 0)
            {
                selectedItem.Name = txtName.Text;
                selectedItem.Description = txtDescription.Text;
                selectedItem.SpriteName = cmbSpriteName.SelectedItem?.ToString() ?? "";
                selectedItem.Effect = cmbEffect.SelectedItem?.ToString() ?? "";
                selectedItem.Status = cmbStatus.SelectedItem?.ToString() ?? "";
                selectedItem.Amount = (int)numAmount.Value;
                selectedItem.BoostTime = (int)numBoostTime.Value;
                selectedItem.WeightGain = (int)numWeightGain.Value;
                selectedItem.ComponentItem = cmbComponentItem.SelectedItem?.ToString() ?? "";
            }

            // Ensure all items have an id
            foreach (var item in items)
            {
                if (string.IsNullOrWhiteSpace(item.Id))
                    item.Id = Guid.NewGuid().ToString();
            }

            string itemPath = Path.Combine(modulePath, "item.json");
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
            };
            var obj = new { item = items };
            try
            {
                string json = JsonSerializer.Serialize(obj, options);
                File.WriteAllText(itemPath, json);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error saving item.json: " + ex.Message);
            }
        }

        #endregion

        #region Helper Methods

        /// <summary>
        /// Updates the component item combo box based on the selected effect.
        /// </summary>
        private void UpdateComponentItemCombo()
        {
            var effect = cmbEffect.SelectedItem?.ToString();
            cmbComponentItem.Items.Clear();
            cmbComponentItem.Items.Add("");
            if (effect == "component")
            {
                foreach (var item in items)
                    cmbComponentItem.Items.Add(item.Name);
                cmbComponentItem.Enabled = true;
            }
            else
            {
                cmbComponentItem.Enabled = false;
                cmbComponentItem.SelectedIndex = 0;
            }
        }

        #endregion
    }
}