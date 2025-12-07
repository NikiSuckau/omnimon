using OmnipetModuleEditor.Controls;
using OmnipetModuleEditor.Models;
using OmnipetModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnipetModuleEditor.Tabs
{
    /// <summary>
    /// Tab for managing and editing battle enemies in the module.
    /// </summary>
    public partial class BattleTab : UserControl
    {
        // Fields
        private List<BattleEnemy> enemies;
        private string modulePath;
        private Module module;
        private EnemyListPanel enemyListPanel;
        private EnemyEditPanel enemyEditPanel;
        private BattleEnemy copiedEnemy = null;
        private Button btnFastEditor;
        private PetSpritePanel spritePanel;
        private Panel selectedPanel = null;
        private BattleEnemy selectedEnemy = null;

        /// <summary>
        /// Initializes a new instance of the <see cref="BattleTab"/> class.
        /// </summary>
        public BattleTab()
        {
            InitializeComponent();
            enemyListPanel.BtnRemove.Click += BtnRemove_Click;
            enemyListPanel.BtnCopy.Click += BtnCopy_Click;
            enemyListPanel.BtnPaste.Click += BtnPaste_Click;
            enemyListPanel.BtnAdd.Click += BtnAdd_Click;
            btnFastEditor.Click += BtnFastEditor_Click;
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

            enemyListPanel = new EnemyListPanel();
            enemyListPanel.Width = 320;
            enemyListPanel.MinimumSize = new Size(320, 0);

            var rightPanel = new Panel { Dock = DockStyle.Fill, Padding = new Padding(0) };

            spritePanel = new PetSpritePanel
            {
                Dock = DockStyle.Top,
                Height = 150
            };

            enemyEditPanel = new EnemyEditPanel
            {
                Dock = DockStyle.Fill
            };

            btnFastEditor = new Button
            {
                Text = Properties.Resources.BattleTab_Button_FastEditor ?? "Fast Editor",
                Width = 140,
                Height = 32,
                Margin = new Padding(8, 16, 8, 8),
                Anchor = AnchorStyles.Right
            };
            var bottomPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Bottom,
                FlowDirection = FlowDirection.RightToLeft,
                AutoSize = true
            };
            bottomPanel.Controls.Add(btnFastEditor);

            rightPanel.Controls.Add(enemyEditPanel);
            rightPanel.Controls.Add(spritePanel);
            rightPanel.Controls.Add(bottomPanel);

            mainLayout.Controls.Add(enemyListPanel, 0, 0);
            mainLayout.Controls.Add(rightPanel, 1, 0);

            this.Controls.Add(mainLayout);
            this.Name = "BattleTab";
            this.Size = new Size(800, 560);
            this.ResumeLayout(false);
        }

        #endregion

        #region Public API

        /// <summary>
        /// Sets the module path and loads enemies and related data.
        /// </summary>
        public void SetModule(string modulePath, Module module)
        {
            this.modulePath = modulePath;
            this.module = module;
            LoadEnemiesFromJson();
            enemyEditPanel.LoadAtkSprites(modulePath);
            enemyEditPanel.PopulateAtkCombos();
            enemyEditPanel.LoadItems(modulePath);
        }

        /// <summary>
        /// Saves the enemies to battle.json.
        /// </summary>
        public void Save()
        {
            if (string.IsNullOrEmpty(modulePath) || enemies == null)
                return;

            string battlePath = Path.Combine(modulePath, "battle.json");
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
            };
            var obj = new { enemies = enemies };
            try
            {
                string json = JsonSerializer.Serialize(obj, options);
                File.WriteAllText(battlePath, json);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.BattleTab_ErrorSaving ?? "Error saving battle.json: {0}", ex.Message),
                    Properties.Resources.Error ?? "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }

        #endregion

        #region Data Loading

        /// <summary>
        /// Loads enemies from battle.json.
        /// </summary>
        private void LoadEnemiesFromJson()
        {
            string battlePath = Path.Combine(this.modulePath, "battle.json");
            enemies = new List<BattleEnemy>();
            enemyListPanel.PanelEnemyList.Controls.Clear();

            if (File.Exists(battlePath))
            {
                try
                {
                    string json = File.ReadAllText(battlePath);
                    using (JsonDocument doc = JsonDocument.Parse(json))
                    {
                        var root = doc.RootElement;
                        if (root.TryGetProperty("enemies", out var enemiesElement))
                        {
                            enemies = JsonSerializer.Deserialize<List<BattleEnemy>>(enemiesElement.GetRawText());
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        string.Format(Properties.Resources.BattleTab_ErrorLoading ?? "Error loading battle.json: {0}", ex.Message),
                        Properties.Resources.Error ?? "Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                }
            }

            if (enemies != null)
                PopulateEnemyPanel();
        }

        #endregion

        #region UI Population

        /// <summary>
        /// Populates the enemy list panel with enemy panels.
        /// </summary>
        private void PopulateEnemyPanel()
        {
            var scrollPos = enemyListPanel.PanelEnemyList.AutoScrollPosition;
            enemyListPanel.PanelEnemyList.Controls.Clear();
            int y = 0;
            foreach (var enemy in enemies)
            {
                var enemyPanel = CreateEnemyPanel(enemy, y);
                enemyListPanel.PanelEnemyList.Controls.Add(enemyPanel);
                y += 56;
            }
            enemyListPanel.PanelEnemyList.AutoScrollPosition = new Point(-scrollPos.X, -scrollPos.Y);
        }

        /// <summary>
        /// Creates a panel for a single enemy.
        /// </summary>
        private Panel CreateEnemyPanel(BattleEnemy enemy, int y)
        {
            var itemPanel = new Panel
            {
                Location = new Point(0, y),
                Size = new Size(enemyListPanel.PanelEnemyList.Width - 20, 56),
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.White,
                Tag = enemy
            };

            itemPanel.Click += (s, e) => SelectEnemyPanel(itemPanel);

            PictureBox pb = new PictureBox
            {
                Location = new Point(4, 4),
                Size = new Size(48, 48),
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = GetAttributeColor(enemy.Attribute ?? ""),
                BorderStyle = BorderStyle.FixedSingle
            };

            // Use new SpriteUtils system for loading enemy sprites with high definition support
            bool moduleHighDefinitionSprites = module?.HighDefinitionSprites ?? false;
            var sprite = SpriteUtils.LoadSingleSprite(enemy.Name, modulePath, module?.NameFormat ?? SpriteUtils.DefaultNameFormat, moduleHighDefinitionSprites);
            pb.Image = sprite;

            itemPanel.Controls.Add(pb);

            Label lblName = new Label
            {
                Text = enemy.Name,
                Location = new Point(60, 4),
                AutoSize = true,
                Font = new Font(Font.FontFamily, 11, FontStyle.Bold),
                ForeColor = Color.DeepSkyBlue
            };

            itemPanel.Controls.Add(lblName);

            Label lblInfo = new Label
            {
                Text = string.Format(Properties.Resources.BattleTab_Label_Info ?? "Ver. {0} | Stage {1} | Area {2} | Round {3}", enemy.Version, enemy.Stage, enemy.Area, enemy.Round),
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
        /// Selects the given enemy panel and loads its data for editing.
        /// </summary>
        private void SelectEnemyPanel(Panel panel)
        {
            if (selectedPanel != null)
                selectedPanel.BackColor = Color.White;

            selectedPanel = panel;
            selectedPanel.BackColor = Color.LightBlue;

            selectedEnemy = panel.Tag as BattleEnemy;
            enemyEditPanel.LoadEnemy(selectedEnemy);

            // Update the sprite panel
            spritePanel.CurrentPet = new Pet
            {
                Name = selectedEnemy.Name,
                Stage = selectedEnemy.Stage,
                Version = selectedEnemy.Version,
                AtkMain = selectedEnemy.AtkMain,
                AtkAlt = selectedEnemy.AtkAlt,
                Attribute = selectedEnemy.Attribute,
                Power = selectedEnemy.Power,
                Hp = selectedEnemy.Hp
            };
            spritePanel.CurrentModule = module;
            spritePanel.ModulePath = modulePath;
            spritePanel.RefreshSprites();
        }

        #endregion

        #region Utility

        /// <summary>
        /// Returns the color for the given attribute.
        /// </summary>
        private Color GetAttributeColor(string attr)
        {
            switch (attr)
            {
                case "Da": return Color.FromArgb(66, 165, 245);      // Data
                case "Va": return Color.FromArgb(102, 187, 106);     // Vaccine
                case "Vi": return Color.FromArgb(237, 83, 80);       // Virus
                case "": return Color.FromArgb(171, 71, 188);        // Free
                default: return Color.FromArgb(171, 71, 188);        // Free (fallback)
            }
        }

        /// <summary>
        /// Utility function to clone a BattleEnemy.
        /// </summary>
        private BattleEnemy CloneEnemy(BattleEnemy enemy)
        {
            return new BattleEnemy
            {
                Name = enemy.Name,
                Power = enemy.Power,
                Stage = enemy.Stage,
                Attribute = enemy.Attribute,
                Hp = enemy.Hp,
                Area = enemy.Area,
                Round = enemy.Round,
                Version = enemy.Version,
                Handicap = enemy.Handicap,
                Prize = enemy.Prize,
                Unlock = enemy.Unlock,
                AtkMain = enemy.AtkMain,
                AtkAlt = enemy.AtkAlt
            };
        }

        #endregion

        #region Button Event Handlers

        private void BtnFastEditor_Click(object sender, EventArgs e)
        {
            var fastEditor = new EnemyFastEditorForm();
            fastEditor.SetModulePath(this.modulePath);
            fastEditor.SetEnemies(this.enemies);

            fastEditor.EnemiesSaved += (newEnemies) =>
            {
                this.enemies = newEnemies;
                PopulateEnemyPanel();
                Save();
            };

            fastEditor.ShowDialog();
        }

        private void BtnRemove_Click(object sender, EventArgs e)
        {
            if (selectedEnemy == null) return;
            var result = MessageBox.Show(
                string.Format(Properties.Resources.BattleTab_ConfirmRemove ?? "Do you want to remove the enemy \"{0}\"?", selectedEnemy.Name),
                Properties.Resources.Confirmation ?? "Confirmation",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning
            );
            if (result == DialogResult.Yes)
            {
                enemies.Remove(selectedEnemy);
                selectedEnemy = null;
                selectedPanel = null;
                PopulateEnemyPanel();
                Save();
            }
        }

        private void BtnCopy_Click(object sender, EventArgs e)
        {
            if (selectedEnemy == null) return;
            copiedEnemy = CloneEnemy(selectedEnemy);
        }

        private void BtnPaste_Click(object sender, EventArgs e)
        {
            if (copiedEnemy == null) return;
            var newEnemy = CloneEnemy(copiedEnemy);
            newEnemy.Name += Properties.Resources.BattleTab_CopySuffix ?? " Copy";
            enemies.Add(newEnemy);
            PopulateEnemyPanel();
            Save();
        }

        private void BtnAdd_Click(object sender, EventArgs e)
        {
            // Load pets from monster.json
            List<Pet> pets = new List<Pet>();
            try
            {
                string monsterPath = Path.Combine(modulePath, "monster.json");
                if (File.Exists(monsterPath))
                {
                    string json = File.ReadAllText(monsterPath);
                    using (JsonDocument doc = JsonDocument.Parse(json))
                    {
                        var root = doc.RootElement;
                        if (root.TryGetProperty("monster", out var monstersElement))
                        {
                            pets = JsonSerializer.Deserialize<List<Pet>>(monstersElement.GetRawText());
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.BattleTab_ErrorLoadingMonster ?? "Error loading monster.json: {0}", ex.Message),
                    Properties.Resources.Error ?? "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }

            using (var dlg = new EnemyAddDialog(pets))
            {
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    BattleEnemy newEnemy;
                    if (dlg.SelectedPet == null)
                    {
                        // Custom: create a default enemy
                        newEnemy = new BattleEnemy
                        {
                            Name = Properties.Resources.BattleTab_NewEnemyName ?? "New Enemy",
                            Stage = 0,
                            Version = dlg.SelectedVersion,
                            Power = 10,
                            Hp = 1,
                            Area = 1,
                            Round = 1,
                            Handicap = 0,
                            Prize = "",
                            Unlock = "",
                            AtkMain = 0,
                            AtkAlt = 0,
                            Attribute = ""
                        };
                    }
                    else
                    {
                        // Based on an existing pet
                        var pet = dlg.SelectedPet;
                        newEnemy = new BattleEnemy
                        {
                            Name = pet.Name,
                            Stage = pet.Stage,
                            Version = pet.Version,
                            Power = pet.Power,
                            Hp = pet.Hp,
                            Area = 1,
                            Round = 1,
                            Handicap = 0,
                            Prize = "",
                            Unlock = "",
                            AtkMain = pet.AtkMain,
                            AtkAlt = pet.AtkAlt,
                            Attribute = pet.Attribute
                        };
                    }
                    if (enemies == null)
                        enemies = new List<BattleEnemy>();
                    enemies.Add(newEnemy);
                    PopulateEnemyPanel();
                    Save();
                    // Select the new enemy for editing
                    var lastPanel = enemyListPanel.PanelEnemyList.Controls.Cast<Panel>().LastOrDefault();
                    if (lastPanel != null)
                        SelectEnemyPanel(lastPanel);
                }
            }
        }

        #endregion

        #region Internal Classes

        // Left panel (enemy list and buttons)
        private class EnemyListPanel : UserControl
        {
            public Panel PanelEnemyList { get; private set; }
            public Button BtnAdd { get; private set; }
            public Button BtnRemove { get; private set; }
            public Button BtnCopy { get; private set; }
            public Button BtnPaste { get; private set; }

            public EnemyListPanel()
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

                PanelEnemyList = new Panel
                {
                    Dock = DockStyle.Fill,
                    AutoScroll = true,
                    BackColor = Color.White
                };
                leftLayout.Controls.Add(PanelEnemyList, 0, 0);

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

                BtnAdd.Height = BtnRemove.Height = BtnCopy.Height = BtnPaste.Height = 36;

                panelButtons.Controls.AddRange(new Control[] { BtnAdd, BtnRemove, BtnCopy, BtnPaste });
                leftLayout.Controls.Add(panelButtons, 0, 1);

                this.Controls.Add(leftLayout);
            }
        }

        // Right panel (enemy editing)
        private class EnemyEditPanel : UserControl
        {
            private TextBox TxtName;
            private NumericUpDown NumPower;
            private ComboBox CmbStage;
            private ComboBox CmbAttribute;
            private NumericUpDown NumHp;
            private NumericUpDown NumArea;
            private NumericUpDown NumRound;
            private NumericUpDown NumVersion;
            private NumericUpDown NumHandicap;
            private ComboBox CmbPrize;
            private TextBox TxtUnlock;
            private ComboBox CmbAtkMain;
            private ComboBox CmbAtkAlt;
            private Dictionary<int, Image> atkSprites = new Dictionary<int, Image>();

            public EnemyEditPanel()
            {
                InitializeComponent();
            }

            private void InitializeComponent()
            {
                this.Dock = DockStyle.Fill;
                var rightLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 1,
                    RowCount = 1,
                    BackColor = SystemColors.Control,
                    Padding = new Padding(8)
                };

                // Campos de edi��o (com limite de largura)
                var fieldsPanel = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 2,
                    Padding = new Padding(0, 8, 0, 0),
                    AutoScroll = true
                };
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100F));
                fieldsPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 220F));

                int row = 0;
                void AddField(string label, Control control)
                {
                    var lbl = new Label
                    {
                        Text = label,
                        TextAlign = ContentAlignment.MiddleRight,
                        AutoSize = false,
                        Width = 100,
                        Anchor = AnchorStyles.Right,
                        Margin = new Padding(0, 2, 4, 2)
                    };

                    control.Width = 200;
                    control.MaximumSize = new Size(200, 0);
                    control.Anchor = AnchorStyles.Left;
                    control.Margin = new Padding(0, 2, 8, 2);

                    fieldsPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                    fieldsPanel.Controls.Add(lbl, 0, row);
                    fieldsPanel.Controls.Add(control, 1, row);
                    row++;
                }

                TxtName = new TextBox();
                NumPower = new NumericUpDown { Minimum = 1, Maximum = 999999, Value = 10 };
                CmbStage = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbStage.Items.AddRange(Enum.GetNames(typeof(OmnipetModuleEditor.Models.StageEnum)));
                CmbAttribute = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbAttribute.Items.AddRange(new object[] { "Free", "Data", "Virus", "Vaccine" });
                NumHp = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 1 };
                NumArea = new NumericUpDown { Minimum = 1, Maximum = 999999, Value = 1 };
                NumRound = new NumericUpDown { Minimum = 1, Maximum = 999999, Value = 1 };
                NumVersion = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 1 };
                NumHandicap = new NumericUpDown { Minimum = 0, Maximum = 999999, Value = 0 };
                CmbPrize = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                TxtUnlock = new TextBox();
                CmbAtkMain = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
                CmbAtkAlt = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };

                AddField("Name:", TxtName);
                AddField("Power:", NumPower);
                AddField("Stage:", CmbStage);
                AddField("Attribute:", CmbAttribute);
                AddField("HP:", NumHp);
                AddField("Area:", NumArea);
                AddField("Round:", NumRound);
                AddField("Version:", NumVersion);
                AddField("Handicap:", NumHandicap);
                AddField("Prize:", CmbPrize);
                AddField("Unlock:", TxtUnlock);
                AddField("Main Attack:", CmbAtkMain);
                AddField("Alt Attack:", CmbAtkAlt);

                var buttonPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Top,
                    FlowDirection = FlowDirection.LeftToRight,
                    AutoSize = true
                };
                var btnSave = new Button { Text = "Save", Width = 80, Margin = new Padding(8, 8, 8, 8) };
                var btnCancel = new Button { Text = "Cancel", Width = 80, Margin = new Padding(8, 8, 8, 8) };
                buttonPanel.Controls.Add(btnSave);
                buttonPanel.Controls.Add(btnCancel);
                fieldsPanel.Controls.Add(buttonPanel, 0, row++);
                fieldsPanel.SetColumnSpan(buttonPanel, 2);

                // Eventos dos bot�es
                btnSave.Click += (s, e) =>
                {
                    var battleTab = GetBattleTab();
                    if (battleTab != null)
                    {
                        battleTab.enemyEditPanel.SaveToEnemy(battleTab.selectedEnemy);
                        battleTab.Save();
                        battleTab.PopulateEnemyPanel();

                        // Seleciona novamente o painel do inimigo editado (se ainda existir)
                        var panel = battleTab.enemyListPanel.PanelEnemyList.Controls
                            .OfType<Panel>()
                            .FirstOrDefault(p => p.Tag is BattleEnemy be &&
                                                 be.Name == battleTab.selectedEnemy.Name &&
                                                 be.Area == battleTab.selectedEnemy.Area &&
                                                 be.Round == battleTab.selectedEnemy.Round &&
                                                 be.Version == battleTab.selectedEnemy.Version);
                        if (panel != null)
                            battleTab.SelectEnemyPanel(panel);
                    }
                };
                btnCancel.Click += (s, e) =>
                {
                    if (Parent is TableLayoutPanel parentLayout && parentLayout.Parent is BattleTab battleTab)
                    {
                        // Recarrega os dados do objeto selecionado
                        battleTab.enemyEditPanel.LoadEnemy(battleTab.selectedEnemy);
                    }
                };

                rightLayout.Controls.Add(fieldsPanel, 0, 0);
                this.Controls.Add(rightLayout);

                // Aqui voc� pode adicionar eventos aos bot�es, se desejar.
            }

            private BattleTab GetBattleTab()
            {
                Control c = this;
                while (c != null && !(c is BattleTab))
                    c = c.Parent;
                return c as BattleTab;
            }

            public void LoadEnemy(BattleEnemy enemy)
            {
                if (enemy == null) return;

                TxtName.Text = enemy.Name ?? "";
                NumPower.Value = Math.Max(NumPower.Minimum, Math.Min(enemy.Power, NumPower.Maximum));
                CmbStage.SelectedIndex = enemy.Stage;
                CmbAttribute.SelectedIndex = (int)PetUtils.JsonToAttributeEnum(enemy.Attribute ?? "");
                NumHp.Value = Math.Max(NumHp.Minimum, Math.Min(enemy.Hp, NumHp.Maximum));
                NumArea.Value = Math.Max(NumArea.Minimum, Math.Min(enemy.Area, NumArea.Maximum));
                NumRound.Value = Math.Max(NumRound.Minimum, Math.Min(enemy.Round, NumRound.Maximum));
                NumVersion.Value = Math.Max(NumVersion.Minimum, Math.Min(enemy.Version, NumVersion.Maximum));
                NumHandicap.Value = Math.Max(NumHandicap.Minimum, Math.Min(enemy.Handicap, NumHandicap.Maximum));
                CmbPrize.SelectedItem = enemy.Prize ?? "";
                TxtUnlock.Text = enemy.Unlock ?? "";
                CmbAtkMain.SelectedIndex = Math.Max(0, Math.Min(enemy.AtkMain, CmbAtkMain.Items.Count - 1));
                CmbAtkAlt.SelectedIndex = Math.Max(0, Math.Min(enemy.AtkAlt, CmbAtkAlt.Items.Count - 1));
            }

            public void LoadAtkSprites(string modulePath)
            {
                this.atkSprites = PetUtils.LoadAtkSprites(modulePath);
            }

            public void PopulateAtkCombos()
            {
                CmbAtkMain.Items.Clear();
                CmbAtkAlt.Items.Clear();
                CmbAtkMain.Items.Add(new AtkComboItem(0, null));
                CmbAtkAlt.Items.Add(new AtkComboItem(0, null));
                
                // Use all available attack sprites instead of hardcoding to 117
                foreach (var kvp in atkSprites.OrderBy(x => x.Key))
                {
                    var item = new AtkComboItem(kvp.Key, kvp.Value);
                    CmbAtkMain.Items.Add(item);
                    CmbAtkAlt.Items.Add(item);
                }
            }

            public void SaveToEnemy(BattleEnemy enemy)
            {
                if (enemy == null) return;
                enemy.Name = TxtName.Text;
                enemy.Power = (int)NumPower.Value;
                enemy.Stage = CmbStage.SelectedIndex;
                enemy.Attribute = CmbAttribute.SelectedIndex >= 0 ? PetUtils.AttributeEnumToJson((AttributeEnum)CmbAttribute.SelectedIndex) : "";
                enemy.Hp = (int)NumHp.Value;
                enemy.Area = (int)NumArea.Value;
                enemy.Round = (int)NumRound.Value;
                enemy.Version = (int)NumVersion.Value;
                enemy.Handicap = (int)NumHandicap.Value;
                enemy.Prize = CmbPrize.SelectedItem?.ToString() ?? "";
                enemy.Unlock = TxtUnlock.Text;
                enemy.AtkMain = CmbAtkMain.SelectedIndex;
                enemy.AtkAlt = CmbAtkAlt.SelectedIndex;
            }

            public void LoadItems(string modulePath)
            {
                CmbPrize.Items.Clear();
                CmbPrize.Items.Add(""); // Adiciona op��o vazia primeiro
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
                                var items = JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText());
                                if (items != null)
                                {
                                    foreach (var item in items)
                                        CmbPrize.Items.Add(item.Name);
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error loading item.json: " + ex.Message);
                    }
                }
            }

            // Classe auxiliar para mostrar n�mero + sprite
            private class AtkComboItem
            {
                public int Number { get; }
                public Image Sprite { get; }
                public AtkComboItem(int number, Image sprite)
                {
                    Number = number;
                    Sprite = sprite;
                }
                public override string ToString() => Number == 0 ? "None" : Number.ToString();
            }
        }

        #endregion
    }
}