using OmnimonModuleEditor.Controls;
using OmnimonModuleEditor.Models;
using OmnimonModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnimonModuleEditor.Tabs
{
    /// <summary>
    /// Tab for managing and editing pets in the module.
    /// </summary>
    public partial class PetTab : UserControl
    {
        // Fields
        private List<Pet> pets;
        private string modulePath;
        private Module module;
        private PetListPanel petListPanel;
        private PetEditPanel petEditPanel;
        private Pet copiedPet = null;
        private PetSpritePanel spritePanel;
        private Panel selectedPanel = null;
        private Pet selectedPet = null;

        /// <summary>
        /// Initializes a new instance of the <see cref="PetTab"/> class.
        /// </summary>
        public PetTab()
        {
            InitializeComponent();
            petListPanel.BtnRemove.Click += BtnRemove_Click;
            petListPanel.BtnCopy.Click += BtnCopy_Click;
            petListPanel.BtnPaste.Click += BtnPaste_Click;
            petListPanel.BtnAdd.Click += BtnAdd_Click;
        }

        #region Initialization

        /// <summary>
        /// Initializes the layout and child controls.
        /// </summary>
        private void InitializeComponent()
        {
            this.SuspendLayout();

            var mainLayout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 1,
                Padding = new Padding(8),
                BackColor = SystemColors.Control
            };
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 320));
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 70F));

            petListPanel = new PetListPanel();
            petEditPanel = new PetEditPanel();

            mainLayout.Controls.Add(petListPanel, 0, 0);
            mainLayout.Controls.Add(petEditPanel, 1, 0);

            this.Controls.Add(mainLayout);
            this.Name = "PetTab";
            this.Size = new Size(800, 560);
            this.ResumeLayout(false);
        }

        #endregion

        #region Public API

        /// <summary>
        /// Sets the module path and loads pets and attack sprites.
        /// </summary>
        public void SetModule(string modulePath, Module module)
        {
            this.modulePath = modulePath;
            this.module = module;
            pets = PetUtils.LoadPetsFromJson(modulePath);
            petEditPanel.LoadAtkSprites(modulePath);
            petEditPanel.PopulateAtkCombos();
            PopulatePetPanel();
        }

        /// <summary>
        /// Saves the pets to monster.json.
        /// </summary>
        public void Save()
        {
            if (string.IsNullOrEmpty(modulePath) || pets == null)
                return;

            string monsterPath = Path.Combine(modulePath, "monster.json");
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
            };
            var obj = new { monster = pets };
            try
            {
                string json = JsonSerializer.Serialize(obj, options);
                File.WriteAllText(monsterPath, json);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.ErrorSavingMonster, ex.Message),
                    Properties.Resources.Error,
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }

        #endregion

        #region UI Population

        /// <summary>
        /// Populates the pet list panel with pet panels.
        /// </summary>
        private void PopulatePetPanel()
        {
            var scrollPos = petListPanel.PanelPetList.AutoScrollPosition;
            petListPanel.PanelPetList.Controls.Clear();
            int y = 0;
            foreach (var pet in pets)
            {
                var petPanel = CreatePetPanel(pet, y);
                petListPanel.PanelPetList.Controls.Add(petPanel);
                y += 56;
            }
            petListPanel.PanelPetList.AutoScrollPosition = new Point(-scrollPos.X, -scrollPos.Y);
        }

        /// <summary>
        /// Populates the pet list and returns the panel for a specific pet.
        /// </summary>
        private Panel PopulatePetPanelAndReturnPanel(Pet petToSelect = null)
        {
            var scrollPos = petListPanel.PanelPetList.AutoScrollPosition;
            petListPanel.PanelPetList.Controls.Clear();
            int y = 0;
            Panel selected = null;
            foreach (var pet in pets)
            {
                var petPanel = CreatePetPanel(pet, y);
                petListPanel.PanelPetList.Controls.Add(petPanel);
                if (petToSelect != null && pet == petToSelect)
                    selected = petPanel;
                y += 56;
            }
            petListPanel.PanelPetList.AutoScrollPosition = new Point(-scrollPos.X, -scrollPos.Y);
            return selected;
        }

        /// <summary>
        /// Creates a panel for a single pet.
        /// </summary>
        private Panel CreatePetPanel(Pet pet, int y)
        {
            var itemPanel = new Panel
            {
                Location = new Point(0, y),
                Size = new Size(petListPanel.PanelPetList.Width - 20, 56),
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.White,
                Tag = pet
            };

            itemPanel.Click += (s, e) => SelectPetPanel(itemPanel);

            PictureBox pb = new PictureBox
            {
                Location = new Point(4, 4),
                Size = new Size(48, 48),
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = PetUtils.GetAttributeColor(pet.Attribute ?? ""),
                BorderStyle = BorderStyle.FixedSingle
            };

            // Use new sprite loading system with module support
            var sprite = PetUtils.LoadSinglePetSprite(pet.Name, modulePath, module);
            pb.Image = sprite;

            itemPanel.Controls.Add(pb);

            Label lblName = new Label
            {
                Text = pet.Name,
                Location = new Point(60, 4),
                AutoSize = true,
                Font = new Font(Font.FontFamily, 11, FontStyle.Bold),
                ForeColor = Color.DeepSkyBlue
            };

            itemPanel.Controls.Add(lblName);

            Label lblInfo = new Label
            {
                Text = string.Format(Properties.Resources.Label_VersionStage ?? "Ver. {0} | Stage {1}", pet.Version, pet.Stage),
                Location = new Point(60, 28),
                AutoSize = true,
                Font = new Font(Font.FontFamily, 8, FontStyle.Regular),
                ForeColor = Color.DeepSkyBlue
            };

            itemPanel.Controls.Add(lblInfo);

            return itemPanel;
        }

        #endregion

        #region Selection

        /// <summary>
        /// Selects the given pet panel and loads its data for editing.
        /// </summary>
        private void SelectPetPanel(Panel panel)
        {
            if (selectedPanel != null)
                selectedPanel.BackColor = Color.White;

            selectedPanel = panel;
            selectedPanel.BackColor = Color.LightBlue;

            selectedPet = panel.Tag as Pet;
            petEditPanel.LoadPet(selectedPet);
            petEditPanel.LoadPetSprites(selectedPet, modulePath, module);
        }

        #endregion

        #region Utility

        /// <summary>
        /// Sorts the pets list.
        /// </summary>
        private void SortPets()
        {
            PetUtils.SortPets(pets);
        }

        #endregion

        #region Button Event Handlers

        private void BtnRemove_Click(object sender, EventArgs e)
        {
            if (selectedPet == null) return;
            var result = MessageBox.Show(
                string.Format(Properties.Resources.ConfirmRemovePet, selectedPet.Name),
                Properties.Resources.Confirmation,
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning
            );
            if (result == DialogResult.Yes)
            {
                pets.Remove(selectedPet);
                selectedPet = null;
                selectedPanel = null;
                SortPets();
                PopulatePetPanel();
                Save();
            }
        }

        private void BtnCopy_Click(object sender, EventArgs e)
        {
            if (selectedPet == null) return;
            copiedPet = PetUtils.ClonePet(selectedPet);
        }

        private void BtnPaste_Click(object sender, EventArgs e)
        {
            if (copiedPet == null) return;
            var newPet = PetUtils.ClonePet(copiedPet);
            newPet.Name += Properties.Resources.PetTab_CopySuffix ?? " Copy";
            pets.Add(newPet);
            SortPets();
            var panel = PopulatePetPanelAndReturnPanel(newPet);
            if (panel != null)
                SelectPetPanel(panel);
            Save();
        }

        private void BtnAdd_Click(object sender, EventArgs e)
        {
            using (var dlg = new StageSelectForm())
            {
                if (dlg.ShowDialog(this) == DialogResult.OK && dlg.SelectedStage >= 0 && dlg.SelectedStage <= 8)
                {
                    var template = OmnimonModuleEditor.Models.PetTemplates.ByStage[dlg.SelectedStage];
                    var newPet = PetUtils.ClonePet(template);
                    newPet.Name = Properties.Resources.PetTab_NewPetName ?? "New Pet";
                    newPet.Stage = dlg.SelectedStage;
                    pets.Add(newPet);
                    SortPets();
                    var panel = PopulatePetPanelAndReturnPanel(newPet);
                    if (panel != null)
                        SelectPetPanel(panel);
                    Save();
                }
            }
        }

        #endregion

        #region Internal Classes

        // Left panel (pet list and buttons)
        private class PetListPanel : UserControl
        {
            public Panel PanelPetList { get; private set; }
            public Button BtnAdd { get; private set; }
            public Button BtnRemove { get; private set; }
            public Button BtnCopy { get; private set; }
            public Button BtnPaste { get; private set; }

            public PetListPanel()
            {
                InitializeComponent();
            }

            private void InitializeComponent()
            {
                this.Dock = DockStyle.Fill;
                var leftLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 1,
                    RowCount = 2,
                    BackColor = SystemColors.ControlLight
                };
                leftLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
                leftLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));

                PanelPetList = new Panel
                {
                    Dock = DockStyle.Fill,
                    AutoScroll = true,
                    BackColor = Color.White
                };
                leftLayout.Controls.Add(PanelPetList, 0, 0);

                var panelButtons = new FlowLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    FlowDirection = FlowDirection.LeftToRight,
                    Padding = new Padding(4),
                    AutoSize = false,
                    AutoSizeMode = AutoSizeMode.GrowAndShrink,
                    WrapContents = false
                };

                BtnAdd = new Button { Text = "Add", Width = 70, Margin = new Padding(0, 0, 4, 0) };
                BtnRemove = new Button { Text = "Remove", Width = 70, Margin = new Padding(0, 0, 4, 0) };
                BtnCopy = new Button { Text = "Copy", Width = 70, Margin = new Padding(0, 0, 4, 0) };
                BtnPaste = new Button { Text = "Paste", Width = 70, Margin = new Padding(0, 0, 4, 0) };

                panelButtons.Controls.AddRange(new Control[] { BtnAdd, BtnRemove, BtnCopy, BtnPaste });
                leftLayout.Controls.Add(panelButtons, 0, 1);

                this.Controls.Add(leftLayout);
            }
        }

        // Right panel (pet editing)
        private class PetEditPanel : UserControl
        {
            public TableLayoutPanel SpritePanel { get; private set; }
            public Button BtnRefresh { get; private set; }
            public Button BtnDownload { get; private set; }
            public Button BtnImport { get; private set; }

            // Editing fields
            public TextBox TxtName;
            public ComboBox CmbStage;
            public NumericUpDown NumVersion;
            public CheckBox ChkSpecial;
            public TextBox TxtSpecialKey;
            public MaskedTextBox TxtSleeps;
            public MaskedTextBox TxtWakes;
            public ComboBox CmbAtkMain;
            public ComboBox CmbAtkAlt;
            public NumericUpDown NumTime;
            public NumericUpDown NumPoopTimer;
            public NumericUpDown NumEnergy;
            public NumericUpDown NumMinWeight;
            public NumericUpDown NumEvolWeight;
            public NumericUpDown NumStomach;
            public NumericUpDown NumHungerLoss;
            public NumericUpDown NumStrengthLoss;
            public NumericUpDown NumHealDoses;
            public NumericUpDown NumPower;
            public ComboBox CmbAttribute;
            public NumericUpDown NumConditionHearts;
            public CheckBox ChkJogress;
            public NumericUpDown NumHp;

            // VB-specific fields - NEW
            public NumericUpDown NumStar;
            public NumericUpDown NumAttack;
            public NumericUpDown NumCriticalTurn;

            private Button btnSave;
            private Button btnCancel;

            private Pet currentPet;

            private List<Panel> spriteBoxes = new List<Panel>();

            private Dictionary<int, Image> atkSprites = new Dictionary<int, Image>();

            private Button btnEditEvolutions; // Adicione este campo

            public PetEditPanel()
            {
                InitializeComponent();
            }

            public void LoadPet(Pet pet)
            {
                if (pet == null) return;
                currentPet = pet;

                TxtName.Text = pet.Name ?? "";
                CmbStage.SelectedIndex = pet.Stage;
                NumVersion.Value = pet.Version;
                ChkSpecial.Checked = pet.Special;
                TxtSpecialKey.Text = pet.SpecialKey ?? "";

                // Normalize to HH:mm format
                TxtSleeps.Text = NormalizeTime(pet.Sleeps);
                TxtWakes.Text = NormalizeTime(pet.Wakes);

                CmbAtkMain.SelectedIndex = Math.Max(0, Math.Min(pet.AtkMain, 117));
                CmbAtkAlt.SelectedIndex = Math.Max(0, Math.Min(pet.AtkAlt, 117));
                NumTime.Value = Math.Max(NumTime.Minimum, pet.Time);
                NumPoopTimer.Value = Math.Max(NumPoopTimer.Minimum, pet.PoopTimer);
                NumEnergy.Value = Math.Max(NumEnergy.Minimum, pet.Energy);
                NumMinWeight.Value = Math.Max(NumMinWeight.Minimum, pet.MinWeight);
                NumEvolWeight.Value = Math.Max(NumEvolWeight.Minimum, pet.EvolWeight);
                NumStomach.Value = Math.Max(NumStomach.Minimum, pet.Stomach);
                NumHungerLoss.Value = Math.Max(NumHungerLoss.Minimum, pet.HungerLoss);
                NumStrengthLoss.Value = Math.Max(NumStrengthLoss.Minimum, pet.StrengthLoss);
                NumHealDoses.Value = Math.Max(NumHealDoses.Minimum, pet.HealDoses);
                NumPower.Value = Math.Max(NumPower.Minimum, pet.Power);
                CmbAttribute.SelectedItem = pet.Attribute ?? "";
                CmbAttribute.SelectedIndex = (int)PetUtils.JsonToAttributeEnum(pet.Attribute ?? "");
                NumConditionHearts.Value = Math.Max(NumConditionHearts.Minimum, pet.ConditionHearts);
                ChkJogress.Checked = pet.JogressAvaliable;
                NumHp.Value = Math.Max(NumHp.Minimum, pet.Hp);

                // VB-specific fields - NEW
                NumStar.Value = Math.Max(NumStar.Minimum, pet.Star);
                NumAttack.Value = Math.Max(NumAttack.Minimum, pet.Attack);
                NumCriticalTurn.Value = Math.Max(NumCriticalTurn.Minimum, pet.CriticalTurn);
            }

            // Helper to normalize time format
            private string NormalizeTime(string value)
            {
                if (string.IsNullOrWhiteSpace(value)) return "";
                if (TimeSpan.TryParse(value, out var ts))
                    return ts.ToString(@"hh\:mm");
                return value;
            }

            public void SaveToPet(Pet pet)
            {
                if (pet == null) return;

                pet.Name = TxtName.Text;
                pet.Stage = CmbStage.SelectedIndex;
                pet.Version = (int)NumVersion.Value;
                pet.Special = ChkSpecial.Checked;
                pet.SpecialKey = TxtSpecialKey.Text;

                // Salva null se vazio, inválido ou igual a "  :"
                pet.Sleeps = IsValidTime(TxtSleeps.Text) ? TxtSleeps.Text : null;
                pet.Wakes = IsValidTime(TxtWakes.Text) ? TxtWakes.Text : null;

                pet.AtkMain = CmbAtkMain.SelectedIndex;
                pet.AtkAlt = CmbAtkAlt.SelectedIndex;
                pet.Time = (int)NumTime.Value;
                pet.PoopTimer = (int)NumPoopTimer.Value;
                pet.Energy = (int)NumEnergy.Value;
                pet.MinWeight = (int)NumMinWeight.Value;
                pet.EvolWeight = (int)NumEvolWeight.Value;
                pet.Stomach = (int)NumStomach.Value;
                pet.HungerLoss = (int)NumHungerLoss.Value;
                pet.StrengthLoss = (int)NumStrengthLoss.Value;
                pet.HealDoses = (int)NumHealDoses.Value;
                pet.Power = (int)NumPower.Value;
                if (CmbAttribute.SelectedIndex >= 0)
                    pet.Attribute = PetUtils.AttributeEnumToJson((AttributeEnum)CmbAttribute.SelectedIndex);
                else
                    pet.Attribute = "";
                pet.ConditionHearts = (int)NumConditionHearts.Value;
                pet.JogressAvaliable = ChkJogress.Checked;
                pet.Hp = (int)NumHp.Value;

                // VB-specific fields - NEW
                pet.Star = (int)NumStar.Value;
                pet.Attack = (int)NumAttack.Value;
                pet.CriticalTurn = (int)NumCriticalTurn.Value;
            }

            // Função auxiliar para validar hora no formato HH:mm
            private bool IsValidTime(string value)
            {
                if (string.IsNullOrWhiteSpace(value)) return false;
                if (value.Trim() == "  :" || value.Trim() == ":") return false;
                TimeSpan ts;
                return TimeSpan.TryParse(value, out ts);
            }

            public void LoadPetSprites(Pet pet, string modulePath, Module module)
            {
                // Clear old images
                for (int i = 0; i < spriteBoxes.Count; i++)
                {
                    var box = spriteBoxes[i];
                    if (box.Controls.Count > 0 && box.Controls[0] is PictureBox pb)
                    {
                        pb.Image = null;
                    }
                    box.BackColor = Color.White;
                }

                if (pet == null || string.IsNullOrEmpty(modulePath)) return;

                // Use new sprite loading system with high definition support
                bool useHighDefinition = module?.HighDefinitionSprites ?? false;
                var spritesDict = SpriteUtils.LoadPetSprites(pet.Name, modulePath, PetUtils.FixedNameFormat, spriteBoxes.Count, useHighDefinition);
                var sprites = SpriteUtils.ConvertSpritesToList(spritesDict, spriteBoxes.Count);

                for (int i = 0; i < spriteBoxes.Count; i++)
                {
                    var box = spriteBoxes[i];

                    PictureBox pb;
                    if (box.Controls.Count == 0)
                    {
                        pb = new PictureBox
                        {
                            Dock = DockStyle.Fill,
                            SizeMode = PictureBoxSizeMode.Zoom,
                            BackColor = Color.White
                        };
                        box.Controls.Add(pb);
                    }
                    else
                    {
                        pb = box.Controls[0] as PictureBox;
                    }

                    if (i < sprites.Count && sprites[i] != null)
                    {
                        pb.Image = sprites[i];
                    }
                    else
                    {
                        pb.Image = null;
                    }
                }
            }

            private void InitializeComponent()
            {
                this.Dock = DockStyle.Fill;
                var rightLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 1,
                    RowCount = 2,
                    BackColor = SystemColors.Control,
                    Padding = new Padding(8)
                };
                rightLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 150F));
                rightLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));

                SpritePanel = new TableLayoutPanel
                {
                    Dock = DockStyle.Top,
                    ColumnCount = 9,
                    RowCount = 4,
                    AutoSize = true,
                    BackColor = Color.Transparent
                };
                for (int i = 0; i < 8; i++)
                    SpritePanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 52F));

                SpritePanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48F));
                SpritePanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 20F));
                SpritePanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 48F));
                SpritePanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 20F));

                string[] spriteLabels = new[]
                {
                    "IDLE1", "IDLE2", "HAPPY", "ANGRY",
                    "TRAIN1", "TRAIN2", "ATK1", "ATK2",
                    "EAT1", "EAT2", "NOPE", "EXTRA",
                    "NAP1", "NAP2", "SICK", "LOSE"
                };

                spriteBoxes.Clear();
                // First row: 8 boxes
                for (int i = 0; i < 8; i++)
                {
                    var box = new Panel
                    {
                        Width = 48,
                        Height = 48,
                        BackColor = Color.White,
                        Margin = new Padding(2),
                        BorderStyle = BorderStyle.FixedSingle
                    };
                    SpritePanel.Controls.Add(box, i, 0);
                    spriteBoxes.Add(box);

                    var lbl = new Label
                    {
                        Text = spriteLabels[i],
                        TextAlign = ContentAlignment.TopCenter,
                        Dock = DockStyle.Top,
                        AutoSize = false,
                        Width = 48,
                        Height = 16,
                        Font = new Font(FontFamily.GenericSansSerif, 7, FontStyle.Regular)
                    };
                    SpritePanel.Controls.Add(lbl, i, 1);
                }
                // Second row: 7 boxes
                for (int i = 0; i < 7; i++)
                {
                    var box = new Panel
                    {
                        Width = 48,
                        Height = 48,
                        BackColor = Color.White,
                        Margin = new Padding(2),
                        BorderStyle = BorderStyle.FixedSingle
                    };
                    SpritePanel.Controls.Add(box, i, 2);
                    spriteBoxes.Add(box);

                    var lbl = new Label
                    {
                        Text = spriteLabels[8 + i],
                        TextAlign = ContentAlignment.TopCenter,
                        Dock = DockStyle.Top,
                        AutoSize = false,
                        Width = 48,
                        Height = 16,
                        Font = new Font(FontFamily.GenericSansSerif, 7, FontStyle.Regular)
                    };
                    SpritePanel.Controls.Add(lbl, i, 3);
                }

                BtnRefresh = new Button
                {
                    Text = "Refresh",
                    Width = 48,
                    Height = 48,
                    Margin = new Padding(2),
                    Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
                };
                SpritePanel.Controls.Add(BtnRefresh, 7, 2);

                BtnImport = new Button
                {
                    Text = "Import",
                    Width = 48,
                    Height = 48,
                    Margin = new Padding(2),
                    Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
                };
                SpritePanel.Controls.Add(BtnImport, 8, 2);

                BtnDownload = new Button
                {
                    Text = "Download",
                    Width = 48,
                    Height = 48,
                    Margin = new Padding(2),
                    Font = new Font(FontFamily.GenericSansSerif, 6.5f, FontStyle.Regular)
                };
                SpritePanel.Controls.Add(BtnDownload, 8, 0);

                var lblEmpty = new Label
                {
                    Text = "",
                    Width = 48,
                    Height = 16
                };
                SpritePanel.Controls.Add(lblEmpty, 7, 3);

                rightLayout.Controls.Add(SpritePanel, 0, 0);

                var fieldsPanel = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 4,
                    Padding = new Padding(0, 8, 0, 0),
                    AutoScroll = true
                };
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 80F));
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 200F));
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120F));
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 200F));

                int row = 0, col = 0;
                void AddField(string label, Control control)
                {
                    if (col >= 2)
                    {
                        col = 0;
                        row++;
                    }

                    fieldsPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                    var lbl = new Label
                    {
                        Text = label,
                        TextAlign = ContentAlignment.MiddleRight,
                        AutoSize = false,
                        Width = 110,
                        Anchor = AnchorStyles.Right,
                        Margin = new Padding(0, 2, 4, 2)
                    };

                    control.Width = 200;
                    control.Anchor = AnchorStyles.Left;
                    control.Margin = new Padding(0, 2, 8, 2);

                    fieldsPanel.Controls.Add(lbl, col * 2, row);
                    fieldsPanel.Controls.Add(control, col * 2 + 1, row);

                    col++;
                }

                // Field instantiation
                TxtName = new TextBox();
                ChkSpecial = new CheckBox();
                TxtSpecialKey = new TextBox(); TxtSpecialKey.Enabled = false;
                ChkSpecial.CheckedChanged += (s, e) => TxtSpecialKey.Enabled = ChkSpecial.Checked;
                CmbStage = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbStage.Items.AddRange(Enum.GetNames(typeof(OmnimonModuleEditor.Models.StageEnum)));
                NumVersion = new NumericUpDown { Minimum = 0, Value = 1 };
                NumTime = new NumericUpDown { Minimum = 1, Value = 1, Maximum = 99999 };
                CmbAttribute = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbAttribute.Items.AddRange(Enum.GetNames(typeof(OmnimonModuleEditor.Models.AttributeEnum)));
                NumEnergy = new NumericUpDown { Minimum = 0, Value = 0 };
                TxtSleeps = new MaskedTextBox { Mask = "00:00" };
                CmbAtkMain = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbAtkAlt = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbAtkMain.DrawMode = DrawMode.OwnerDrawFixed;
                CmbAtkMain.ItemHeight = 36;
                CmbAtkMain.DrawItem += AtkCombo_DrawItem;
                CmbAtkAlt.DrawMode = DrawMode.OwnerDrawFixed;
                CmbAtkAlt.ItemHeight = 36;
                CmbAtkAlt.DrawItem += AtkCombo_DrawItem;
                TxtWakes = new MaskedTextBox { Mask = "00:00" };
                NumPower = new NumericUpDown { Minimum = 0, Value = 0, Maximum = 300 };
                NumHp = new NumericUpDown { Minimum = 0, Value = 0 };
                NumHungerLoss = new NumericUpDown { Minimum = 2, Value = 4, Maximum = 99999 };
                NumStomach = new NumericUpDown { Minimum = 2, Value = 4 };
                NumStrengthLoss = new NumericUpDown { Minimum = 2, Value = 4, Maximum = 99999 };
                NumMinWeight = new NumericUpDown { Minimum = 5, Value = 5 };
                NumEvolWeight = new NumericUpDown { Minimum = 0, Value = 0, Maximum = 99 };
                NumPoopTimer = new NumericUpDown { Minimum = 3, Value = 3, Maximum = 99999 };
                NumConditionHearts = new NumericUpDown { Minimum = 0, Value = 0 };
                NumHealDoses = new NumericUpDown { Minimum = 1, Value = 1 };
                ChkJogress = new CheckBox();

                // VB-specific fields - NEW
                NumStar = new NumericUpDown { Minimum = 0, Value = 0, Maximum = 99 };
                NumAttack = new NumericUpDown { Minimum = 0, Value = 1, Maximum = 99 };
                NumCriticalTurn = new NumericUpDown { Minimum = 0, Value = 0, Maximum = 99 };

                // Add fields
                AddField("Name:", TxtName);
                AddField("Special:", ChkSpecial);
                AddField("Stage:", CmbStage);
                AddField("Special Key:", TxtSpecialKey);
                AddField("Version:", NumVersion);
                AddField("Time:", NumTime);
                AddField("Attribute:", CmbAttribute);
                AddField("Energy:", NumEnergy);
                AddField("Sleeps:", TxtSleeps);
                AddField("ATK Main:", CmbAtkMain);
                AddField("Wakes:", TxtWakes);
                AddField("ATK Alt:", CmbAtkAlt);
                AddField("Power:", NumPower);
                AddField("HP:", NumHp);
                AddField("Hunger Loss:", NumHungerLoss);
                AddField("Stomach:", NumStomach);
                AddField("Strength Loss:", NumStrengthLoss);
                AddField("Min Weight:", NumMinWeight);
                AddField("Poop Timer:", NumPoopTimer);
                AddField("Evol Weight:", NumEvolWeight);
                AddField("Condition Hearts:", NumConditionHearts);
                AddField("Heal Doses:", NumHealDoses);
                AddField("Jogress Available:", ChkJogress);
                // VB-specific fields - NEW
                AddField("Star:", NumStar);
                AddField("Attack:", NumAttack);
                AddField("Critical Turn:", NumCriticalTurn);

                // Save and Cancel buttons
                btnSave = new Button { Text = "Save", Width = 80, Margin = new Padding(8, 8, 8, 8) };
                btnCancel = new Button { Text = "Cancel", Width = 80, Margin = new Padding(8, 8, 8, 8) };
                var buttonPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Top,
                    FlowDirection = FlowDirection.LeftToRight,
                    AutoSize = true
                };
                buttonPanel.Controls.Add(btnSave);
                buttonPanel.Controls.Add(btnCancel);

                // Add button panel to fieldsPanel
                fieldsPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                fieldsPanel.Controls.Add(buttonPanel, 0, ++row);
                fieldsPanel.SetColumnSpan(buttonPanel, 4);

                // Button events
                btnSave.Click += (s, e) =>
                {
                    if (currentPet != null)
                    {
                        SaveToPet(currentPet);
                        if (Parent is TableLayoutPanel parentLayout && parentLayout.Parent is PetTab petTab)
                        {
                            petTab.SortPets();
                            var panel = petTab.PopulatePetPanelAndReturnPanel(currentPet);
                            if (panel != null)
                                petTab.SelectPetPanel(panel);
                            petTab.Save();
                        }
                    }
                };
                btnCancel.Click += (s, e) =>
                {
                    if (currentPet != null)
                        LoadPet(currentPet);
                };

                fieldsPanel.Dock = DockStyle.Fill;
                fieldsPanel.AutoScroll = true;
                rightLayout.Controls.Add(fieldsPanel, 0, 1);

                this.Controls.Add(rightLayout);

                // Refresh button event
                BtnRefresh.Click += (s, e) =>
                {
                    if (Parent is TableLayoutPanel parentLayout && parentLayout.Parent is PetTab petTab)
                    {
                        petTab.petEditPanel.LoadPetSprites(petTab.selectedPet, petTab.modulePath, petTab.module);
                    }
                };

                BtnDownload.Click += (s, e) =>
                {
                    if (currentPet != null && !string.IsNullOrWhiteSpace(currentPet.Name))
                    {
                        try
                        {
                            Clipboard.SetText(currentPet.Name);
                        }
                        catch
                        {
                            MessageBox.Show("Could not copy the name to the clipboard.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
                        MessageBox.Show("Could not open the browser.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                };

                // When populating the ComboBox:
                CmbAttribute.Items.Clear();
                CmbAttribute.Items.AddRange(new object[] { "Free", "Data", "Virus", "Vaccine" });

                BtnImport.Click += (s, e) =>
                {
                    // Access the parent PetTab
                    PetTab petTab = null;
                    if (Parent is TableLayoutPanel parentLayout && parentLayout.Parent is PetTab pt)
                        petTab = pt;

                    if (currentPet == null || petTab == null || string.IsNullOrWhiteSpace(currentPet.Name))
                    {
                        MessageBox.Show("Select a valid pet to import sprites.", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        return;
                    }

                    // Build the expected zip file name using fixed format
                    string zipName = SpriteUtils.GetSpriteName(currentPet.Name, PetUtils.FixedNameFormat) + ".zip";

                    // Get the user's default downloads folder
                    string downloads = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                    string downloadsFolder = Path.Combine(downloads, "Downloads");
                    string zipPath = Path.Combine(downloadsFolder, zipName);

                    if (!File.Exists(zipPath))
                    {
                        MessageBox.Show($"File not found: {zipPath}", "Import sprites", MessageBoxButtons.OK, MessageBoxIcon.Information);
                        return;
                    }

                    var result = MessageBox.Show(
                        $"Import sprites from \"{zipName}\" for this pet?\n\nThe zip file will be copied to the monsters folder.",
                        "Import sprites",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question
                    );
                    if (result != DialogResult.Yes)
                        return;

                    // Determine which monsters folder to use based on high definition setting
                    bool useHighDefinition = petTab.module?.HighDefinitionSprites ?? false;
                    string monstersFolder = useHighDefinition ? "monsters_hidef" : "monsters";
                    string targetFolder = Path.Combine(petTab.modulePath, monstersFolder);
                    
                    if (!Directory.Exists(targetFolder))
                        Directory.CreateDirectory(targetFolder);

                    // Copy the zip file to the appropriate monsters folder
                    string destinationZipPath = Path.Combine(targetFolder, zipName);

                    try
                    {
                        File.Copy(zipPath, destinationZipPath, true);

                        MessageBox.Show("Sprites imported successfully!", "Import sprites", MessageBoxButtons.OK, MessageBoxIcon.Information);

                        // Refresh pet sprites
                        LoadPetSprites(currentPet, petTab.modulePath, petTab.module);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error importing sprites: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                };

                // Bot�o Edit Evolutions
                btnEditEvolutions = new Button
                {
                    Text = "Edit Evolutions",
                    Width = 140,
                    Height = 32,
                    Margin = new Padding(8, 16, 8, 8),
                    Anchor = AnchorStyles.Right
                };

                // Adicione o bot�o ao final do painel de campos
                var bottomPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Bottom,
                    FlowDirection = FlowDirection.RightToLeft,
                    AutoSize = true
                };
                bottomPanel.Controls.Add(btnEditEvolutions);
                this.Controls.Add(bottomPanel);

                // Evento do bot�o
                btnEditEvolutions.Click += (s, e) =>
                {
                    {
                        var tabPage = Parent?.Parent?.Parent as TabPage;
                        var petTab = tabPage?.Controls.OfType<PetTab>().FirstOrDefault();
                        var dlg = new EvolutionsEditorForm(petTab.pets, petTab.modulePath, petTab.module);
                        dlg.ShowDialog(this);
                    }
                };
            }

            public void PopulateAtkCombos()
            {
                // Clear and add item 0 (None)
                CmbAtkMain.Items.Clear();
                CmbAtkAlt.Items.Clear();
                CmbAtkMain.Items.Add(new AtkComboItem(0, null));
                CmbAtkAlt.Items.Add(new AtkComboItem(0, null));
                for (int i = 1; i <= 117; i++)
                {
                    var sprite = atkSprites.ContainsKey(i) ? atkSprites[i] : null;
                    var item = new AtkComboItem(i, sprite);
                    CmbAtkMain.Items.Add(item);
                    CmbAtkAlt.Items.Add(item);
                }
            }

            // Custom draw to show sprite + number
            private void AtkCombo_DrawItem(object sender, DrawItemEventArgs e)
            {
                if (e.Index < 0) return;
                var combo = sender as ComboBox;
                var item = combo.Items[e.Index] as AtkComboItem;
                e.DrawBackground();
                int x = e.Bounds.Left + 2;
                if (item.Sprite != null)
                {
                    e.Graphics.DrawImage(item.Sprite, x, e.Bounds.Top + 2, 32, 32);
                    x += 36;
                }
                using (var brush = new SolidBrush(e.ForeColor))
                {
                    e.Graphics.DrawString(item.ToString(), e.Font, brush, x, e.Bounds.Top + 8);
                }
                e.DrawFocusRectangle();
            }

            internal void LoadAtkSprites(string modulePath)
            {
                this.atkSprites = PetUtils.LoadAtkSprites(modulePath);
            }
        }

        #endregion
    }
}