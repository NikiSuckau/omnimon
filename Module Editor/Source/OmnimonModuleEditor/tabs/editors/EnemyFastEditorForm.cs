using OmnimonModuleEditor.Models;
using OmnimonModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace OmnimonModuleEditor
{
    /// <summary>
    /// Editor window for managing fast enemy areas and rounds.
    /// </summary>
    public partial class EnemyFastEditorForm : Form
    {
        // Data fields
        private List<BattleEnemy> enemies;
        private List<Pet> pets;
        private string modulePath;
        private Module module;

        // UI controls
        private TableLayoutPanel mainLayout;
        private FlowLayoutPanel topBar;
        private ComboBox cmbVersions;
        private ComboBox cmbStages;
        private Button btnAddArea;
        private Button btnSave;
        private Button btnCancel;
        private Panel panelPetList;
        private TabControl tabAreas;

        // State
        private int selectedVersion = -1;
        private int selectedStage = -1;
        private readonly List<AreaGrid> areaGrids = new List<AreaGrid>();
        private readonly List<string> itemList = new List<string>();

        /// <summary>
        /// Initializes a new instance of the <see cref="EnemyFastEditorForm"/> class.
        /// </summary>
        public EnemyFastEditorForm()
        {
            InitializeLayout();
        }

        /// <summary>
        /// Sets the module object for this editor.
        /// </summary>
        public void SetModule(Module module)
        {
            this.module = module;
        }

        /// <summary>
        /// Sets the list of enemies to be edited.
        /// </summary>
        public void SetEnemies(List<BattleEnemy> list)
        {
            enemies = list ?? new List<BattleEnemy>();
            // Descobre o maior índice de área nos inimigos
            int maxArea = enemies.Count > 0 ? enemies.Max(e => e.Area) : 0;
            // Garante que existam abas suficientes
            while (areaGrids.Count < maxArea)
                AddAreaTab();
            // Carrega os inimigos em cada grid
            foreach (var g in areaGrids)
                g.LoadEnemies(enemies);
        }

        /// <summary>
        /// Sets the module path and loads all related data.
        /// </summary>
        public void SetModulePath(string path)
        {
            modulePath = path;
            LoadModule();
            LoadPetsFromJson();
            LoadItemsFromJson();
            PopulateVersionCombo();
            PopulateStageCombo();
            PopulatePetList();
            foreach (var g in areaGrids)
                g.SetItemList(itemList);
            if (areaGrids.Count == 0)
                AddAreaTab();
        }

        #region Layout and UI Initialization

        /// <summary>
        /// Initializes the layout and UI controls.
        /// </summary>
        private void InitializeLayout()
        {
            Text = "Fast Enemy Editor";
            Size = new Size(1100, 700);
            MinimumSize = new Size(900, 600);

            mainLayout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 2,
            };
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 260));
            mainLayout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            Controls.Add(mainLayout);

            topBar = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                Padding = new Padding(8, 8, 8, 8),
                AutoSize = true,
                WrapContents = false
            };

            cmbVersions = new ComboBox { Width = 90, DropDownStyle = ComboBoxStyle.DropDownList };
            cmbStages = new ComboBox { Width = 120, DropDownStyle = ComboBoxStyle.DropDownList };
            btnAddArea = new Button { Text = "Add Area", AutoSize = true };
            btnSave = new Button { Text = "Save", AutoSize = true };
            btnCancel = new Button { Text = "Cancel", AutoSize = true };

            cmbVersions.SelectedIndexChanged += (_, __) =>
            {
                if (cmbVersions.SelectedIndex > 0)
                    selectedVersion = int.Parse(cmbVersions.Text.Replace("Version ", ""));
                else
                    selectedVersion = -1;
                PopulatePetList();
            };

            cmbStages.SelectedIndexChanged += (_, __) =>
            {
                selectedStage = cmbStages.SelectedIndex - 1;
                PopulatePetList();
            };

            btnAddArea.Click += (_, __) => AddAreaTab();
            btnSave.Click += (_, __) => { SaveEnemiesFromGrids(); DialogResult = DialogResult.OK; };
            btnCancel.Click += (_, __) => DialogResult = DialogResult.Cancel;

            topBar.Controls.AddRange(new Control[]
            {
                new Label{Text="Version:", AutoSize=true, Margin=new Padding(0,8,4,0)},
                cmbVersions,
                new Label{Text="Stage:", AutoSize=true, Margin=new Padding(12,8,4,0)},
                cmbStages,
                btnAddArea,
                btnSave,
                btnCancel
            });

            mainLayout.Controls.Add(topBar, 0, 0);
            mainLayout.SetColumnSpan(topBar, 2);

            panelPetList = new Panel
            {
                Dock = DockStyle.Fill,
                AutoScroll = true,
                Padding = new Padding(8),
                BackColor = Color.WhiteSmoke
            };
            mainLayout.Controls.Add(panelPetList, 0, 1);

            tabAreas = new TabControl
            {
                Dock = DockStyle.Fill,
                Alignment = TabAlignment.Top,
                ItemSize = new Size(120, 36),
                SizeMode = TabSizeMode.Fixed
            };
            mainLayout.Controls.Add(tabAreas, 1, 1);
        }

        #endregion

        #region ComboBox Data Population

        /// <summary>
        /// Populates the version combo box.
        /// </summary>
        private void PopulateVersionCombo()
        {
            cmbVersions.Items.Clear();
            cmbVersions.Items.Add("");
            if (pets == null) return;
            foreach (var v in pets.Where(p => p.Power > 0)
                                   .Select(p => p.Version)
                                   .Distinct().OrderBy(v => v))
                cmbVersions.Items.Add($"Version {v}");
            cmbVersions.SelectedIndex = 0;
            selectedVersion = -1;
        }

        /// <summary>
        /// Populates the stage combo box.
        /// </summary>
        private void PopulateStageCombo()
        {
            cmbStages.Items.Clear();
            cmbStages.Items.Add("");
            foreach (var n in Enum.GetNames(typeof(StageEnum)))
                cmbStages.Items.Add(n);
            cmbStages.SelectedIndex = 0;
            selectedStage = -1;
        }

        #endregion

        #region Area Tabs

        /// <summary>
        /// Adds a new area tab to the editor.
        /// </summary>
        private void AddAreaTab()
        {
            int idx = tabAreas.TabPages.Count + 1;
            var page = new TabPage($"Area {idx}");

            var grid = new AreaGrid(GetModuleVersions(), module, modulePath, itemList, idx);
            areaGrids.Add(grid);

            grid.Panel.Dock = DockStyle.Fill;
            page.Controls.Add(grid.Panel);
            tabAreas.TabPages.Add(page);
            tabAreas.SelectedTab = page;
        }

        /// <summary>
        /// Gets the list of module versions.
        /// </summary>
        private List<int> GetModuleVersions() =>
            pets?.Where(p => p.Power > 0)
                 .Select(p => p.Version)
                 .Distinct()
                 .OrderBy(v => v)
                 .ToList() ?? new List<int>();

        #endregion

        #region Pet List

        /// <summary>
        /// Populates the pet list panel with filtered pets.
        /// </summary>
        private void PopulatePetList()
        {
            panelPetList.Controls.Clear();
            if (pets == null) return;

            var filtered = pets.Where(p => p.Power > 0 &&
                                           (selectedVersion == -1 || p.Version == selectedVersion) &&
                                           (selectedStage == -1 || p.Stage == selectedStage))
                               .OrderBy(p => p.Stage)
                               .ThenBy(p => p.Version)
                               .ThenBy(p => p.Name);

            int y = 0;
            foreach (var pet in filtered)
            {
                var p = CreatePetPanel(pet);
                p.Location = new Point(0, y);
                panelPetList.Controls.Add(p);
                y += p.Height + 8;
            }
        }

        /// <summary>
        /// Creates a panel representing a pet for the pet list.
        /// </summary>
        private Panel CreatePetPanel(Pet pet)
        {
            var pnl = new Panel { Size = new Size(230, 56), BorderStyle = BorderStyle.FixedSingle, Tag = pet };
            pnl.Click += (s, e) =>
            {
                if (tabAreas.SelectedIndex >= 0 && tabAreas.SelectedIndex < areaGrids.Count)
                {
                    areaGrids[tabAreas.SelectedIndex].AddEnemyFromPet(pet);
                }
            };

            var pb = new PictureBox
            {
                Location = new Point(4, 4),
                Size = new Size(48, 48),
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = GetAttributeColor(pet.Attribute ?? ""),
                BorderStyle = BorderStyle.FixedSingle
            };

            LoadSpriteIntoPictureBox(pb, pet.Name);

            var name = new Label
            {
                Text = pet.Name,
                Location = new Point(60, 4),
                AutoSize = true,
                Font = new Font(FontFamily.GenericSansSerif, 11, FontStyle.Bold),
                ForeColor = Color.DeepSkyBlue
            };

            var info = new Label
            {
                Text = $"Stage {pet.Stage} | Ver. {pet.Version}",
                Location = new Point(60, 28),
                AutoSize = true,
                Font = new Font(FontFamily.GenericSansSerif, 8),
                ForeColor = Color.DeepSkyBlue
            };

            pnl.Controls.AddRange(new Control[] { pb, name, info });
            return pnl;
        }

        /// <summary>
        /// Loads the pet sprite into the given PictureBox.
        /// </summary>
        private void LoadSpriteIntoPictureBox(PictureBox pb, string petName)
        {
            if (string.IsNullOrEmpty(modulePath)) return;
            
            // Use new sprite loading system with fixed format
            var sprite = SpriteUtils.LoadSingleSprite(petName, modulePath, PetUtils.FixedNameFormat);
            pb.Image = sprite;
        }

        /// <summary>
        /// Gets the color for a given attribute.
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

        #endregion

        #region Save and Data Events

        /// <summary>
        /// Event triggered when enemies are saved.
        /// </summary>
        public event Action<List<BattleEnemy>> EnemiesSaved;

        /// <summary>
        /// Saves the enemies from all area grids.
        /// </summary>
        private void SaveEnemiesFromGrids()
        {
            enemies = areaGrids.SelectMany(g => g.GetAllBattleEnemies()).ToList();
            EnemiesSaved?.Invoke(enemies);
        }

        #endregion

        #region JSON Data Loading

        /// <summary>
        /// Loads the module from module.json.
        /// </summary>
        private void LoadModule()
        {
            if (module != null || string.IsNullOrEmpty(modulePath)) return;
            string f = Path.Combine(modulePath, "module.json");
            if (File.Exists(f))
                try { module = System.Text.Json.JsonSerializer.Deserialize<Module>(File.ReadAllText(f)); }
                catch { module = null; }
        }

        /// <summary>
        /// Loads the pets from monster.json.
        /// </summary>
        private void LoadPetsFromJson()
        {
            pets = new List<Pet>();
            if (string.IsNullOrEmpty(modulePath)) return;
            string f = Path.Combine(modulePath, "monster.json");
            if (!File.Exists(f)) return;
            try
            {
                var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(f));
                if (doc.RootElement.TryGetProperty("monster", out var arr))
                    pets = System.Text.Json.JsonSerializer.Deserialize<List<Pet>>(arr.GetRawText());
            }
            catch { }
        }

        /// <summary>
        /// Loads the item list from item.json.
        /// </summary>
        private void LoadItemsFromJson()
        {
            itemList.Clear();
            if (string.IsNullOrEmpty(modulePath)) return;
            string f = Path.Combine(modulePath, "item.json");
            if (!File.Exists(f)) return;
            try
            {
                var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(f));
                if (doc.RootElement.TryGetProperty("item", out var arr) && arr.ValueKind == System.Text.Json.JsonValueKind.Array)
                    foreach (var i in arr.EnumerateArray())
                        if (i.TryGetProperty("name", out var n)) itemList.Add(n.GetString());
            }
            catch { }
        }

        #endregion

        #region AreaGrid Internal Class

        /// <summary>
        /// Represents a grid for managing enemies in a specific area.
        /// </summary>
        private class AreaGrid
        {
            public Panel Panel { get; }
            private readonly TableLayoutPanel grid;
            private readonly List<int> versions;
            private readonly List<List<BattleEnemy>> enemiesByVersion;
            private readonly Module module;
            private readonly string modulePath;
            private List<string> itemList;
            private readonly int areaIndex;

            private int columnCount = 1;
            private List<TextBox> unlockBoxes = new List<TextBox>();
            private List<ComboBox> itemCombos = new List<ComboBox>();

            public AreaGrid(List<int> versions, Module module, string modulePath, List<string> items, int areaIdx)
            {
                this.versions = versions;
                this.module = module;
                this.modulePath = modulePath;
                this.itemList = items ?? new List<string>();
                areaIndex = areaIdx;
                enemiesByVersion = versions.Select(_ => new List<BattleEnemy>()).ToList();

                Panel = new Panel { Dock = DockStyle.Fill, AutoScroll = true };

                grid = new TableLayoutPanel
                {
                    AutoSize = true,
                    AutoSizeMode = AutoSizeMode.GrowAndShrink,
                    Location = Point.Empty,
                    Anchor = AnchorStyles.Top | AnchorStyles.Left,
                    ColumnCount = 1,
                    RowCount = versions.Count + 2,
                    CellBorderStyle = TableLayoutPanelCellBorderStyle.Single,
                    GrowStyle = TableLayoutPanelGrowStyle.AddColumns
                };

                grid.Controls.Add(MakeHeaderLabel("Round 1"), 0, 0);
                for (int i = 0; i < versions.Count; i++)
                    grid.Controls.Add(MakeHeaderLabel($"Version {versions[i]}", ContentAlignment.MiddleRight), 0, i + 1);

                AddUnlockRow();

                Panel.Controls.Add(grid);
            }

            private static Label MakeHeaderLabel(string txt, ContentAlignment align = ContentAlignment.MiddleCenter) =>
                new Label { Text = txt, TextAlign = align, Dock = DockStyle.Fill, Font = new Font(FontFamily.GenericSansSerif, 9, FontStyle.Bold) };

            private void AddUnlockRow()
            {
                unlockBoxes.Clear();
                itemCombos.Clear();

                for (int c = 0; c < columnCount; c++)
                {
                    var cellPanel = new Panel { Dock = DockStyle.Fill, Height = 70 };
                    var unlockLabel = new Label { Text = "Unlock:", Dock = DockStyle.Top, AutoSize = true, TextAlign = ContentAlignment.MiddleLeft };
                    var unlockBox = new TextBox { Width = 100, Dock = DockStyle.Top, Margin = new Padding(0, 0, 0, 2) };
                    var itemLabel = new Label { Text = "Item:", Dock = DockStyle.Top, AutoSize = true, TextAlign = ContentAlignment.MiddleLeft };
                    var itemCombo = new ComboBox
                    {
                        Width = 100,
                        Dock = DockStyle.Top,
                        DropDownStyle = ComboBoxStyle.DropDownList
                    };
                    itemCombo.Items.Add("");
                    foreach (var item in itemList)
                        itemCombo.Items.Add(item);

                    cellPanel.Controls.Add(itemCombo);
                    cellPanel.Controls.Add(itemLabel);
                    cellPanel.Controls.Add(unlockBox);
                    cellPanel.Controls.Add(unlockLabel);

                    grid.Controls.Add(cellPanel, c, versions.Count + 1);

                    unlockBoxes.Add(unlockBox);
                    itemCombos.Add(itemCombo);
                }
            }

            private void ExpandUnlockRow()
            {
                for (int c = unlockBoxes.Count; c < columnCount; c++)
                {
                    var cellPanel = new Panel { Dock = DockStyle.Fill, Height = 70 };
                    var unlockLabel = new Label { Text = "Unlock:", Dock = DockStyle.Top, AutoSize = true, TextAlign = ContentAlignment.MiddleLeft };
                    var unlockBox = new TextBox { Width = 100, Dock = DockStyle.Top, Margin = new Padding(0, 0, 0, 2) };
                    var itemLabel = new Label { Text = "Item:", Dock = DockStyle.Top, AutoSize = true, TextAlign = ContentAlignment.MiddleLeft };
                    var itemCombo = new ComboBox
                    {
                        Width = 100,
                        Dock = DockStyle.Top,
                        DropDownStyle = ComboBoxStyle.DropDownList
                    };
                    itemCombo.Items.Add("");
                    foreach (var item in itemList)
                        itemCombo.Items.Add(item);

                    cellPanel.Controls.Add(itemCombo);
                    cellPanel.Controls.Add(itemLabel);
                    cellPanel.Controls.Add(unlockBox);
                    cellPanel.Controls.Add(unlockLabel);

                    grid.Controls.Add(cellPanel, c, versions.Count + 1);

                    unlockBoxes.Add(unlockBox);
                    itemCombos.Add(itemCombo);
                }
            }

            private void AddColumn()
            {
                columnCount++;
                grid.ColumnCount = columnCount;
                grid.Controls.Add(MakeHeaderLabel($"Round {columnCount}"), columnCount - 1, 0);
                for (int r = 1; r <= versions.Count; r++)
                    grid.Controls.Add(new Panel { Size = new Size(140, 40) }, columnCount - 1, r);
                ExpandUnlockRow();
            }

            private void PlaceEnemy(BattleEnemy e, int vIdx, int col)
            {
                var cell = grid.GetControlFromPosition(col, vIdx + 1);
                if (cell != null) grid.Controls.Remove(cell);

                var slot = new Panel { Size = new Size(140, 40), BackColor = Color.LightYellow, BorderStyle = BorderStyle.FixedSingle };
                var pb = new PictureBox { Location = new Point(2, 2), Size = new Size(30, 30), SizeMode = PictureBoxSizeMode.Zoom };
                LoadSprite(pb, e.Name);
                var info = new Label
                {
                    Text = $"{e.Name}\nS:{e.Stage} V:{e.Version}\nP:{e.Power}",
                    Location = new Point(34, 0),
                    AutoSize = true,
                    Font = new Font(FontFamily.GenericSansSerif, 7)
                };
                slot.Controls.AddRange(new Control[] { pb, info });

                slot.MouseUp += (s, ev) =>
                {
                    if (ev.Button == MouseButtons.Right)
                    {
                        RemoveEnemyAndShiftLeft(vIdx, col);
                    }
                };

                grid.Controls.Add(slot, col, vIdx + 1);
            }

            private void LoadSprite(PictureBox pb, string name)
            {
                if (string.IsNullOrEmpty(modulePath)) return;
                
                // Use new sprite loading system with fixed format
                var sprite = SpriteUtils.LoadSingleSprite(name, modulePath, PetUtils.FixedNameFormat);
                pb.Image = sprite;
            }

            private BattleEnemy CreateBattleEnemyFromPet(Pet p, int area, int round) => new BattleEnemy
            {
                Name = p.Name,
                Power = p.Power,
                Attribute = p.Attribute,
                Hp = p.Hp,
                Version = p.Version,
                Stage = p.Stage,
                AtkMain = p.AtkMain,
                AtkAlt = p.AtkAlt,
                Area = area,
                Round = round
            };

            /// <summary>
            /// Loads enemies into the grid for this area.
            /// </summary>
            public void LoadEnemies(List<BattleEnemy> all)
            {
                for (int v = 0; v < enemiesByVersion.Count; v++) enemiesByVersion[v].Clear();
                foreach (var be in all.Where(b => b.Area == areaIndex))
                {
                    int vIdx = versions.IndexOf(be.Version); if (vIdx < 0) continue;
                    while (enemiesByVersion[vIdx].Count < be.Round) enemiesByVersion[vIdx].Add(null);
                    if (be.Round > columnCount) while (columnCount < be.Round) AddColumn();
                    enemiesByVersion[vIdx][be.Round - 1] = be;
                }

                for (int v = 0; v < versions.Count; v++)
                    for (int c = 0; c < enemiesByVersion[v].Count; c++)
                        if (enemiesByVersion[v][c] != null) PlaceEnemy(enemiesByVersion[v][c], v, c);

                // Preencher unlock/prize de cada round com o valor do primeiro inimigo daquele round
                for (int c = 0; c < columnCount; c++)
                {
                    var first = all.FirstOrDefault(e => e.Area == areaIndex && e.Round == c + 1);
                    if (first != null)
                    {
                        if (unlockBoxes.Count > c)
                            unlockBoxes[c].Text = first.Unlock ?? "";
                        if (itemCombos.Count > c)
                            itemCombos[c].SelectedItem = first.Prize ?? "";
                    }
                }
            }

            /// <summary>
            /// Gets all battle enemies from this area grid.
            /// </summary>
            public List<BattleEnemy> GetAllBattleEnemies()
            {
                var list = new List<BattleEnemy>();

                for (int c = 0; c < columnCount; c++)
                {
                    string unlock = unlockBoxes.Count > c ? unlockBoxes[c].Text : "";
                    string prize = itemCombos.Count > c ? (itemCombos[c].SelectedItem as string ?? "") : "";

                    if (!string.IsNullOrEmpty(unlock) || !string.IsNullOrEmpty(prize))
                    {
                        for (int v = 0; v < versions.Count; v++)
                        {
                            if (enemiesByVersion[v].Count > c && enemiesByVersion[v][c] != null)
                            {
                                if (!string.IsNullOrEmpty(unlock))
                                    enemiesByVersion[v][c].Unlock = unlock;
                                if (!string.IsNullOrEmpty(prize))
                                    enemiesByVersion[v][c].Prize = prize;
                            }
                        }
                    }
                }

                for (int v = 0; v < versions.Count; v++)
                {
                    for (int c = 0; c < enemiesByVersion[v].Count; c++)
                    {
                        var be = enemiesByVersion[v][c];
                        if (be != null && !string.IsNullOrWhiteSpace(be.Name))
                        {
                            be.Area = areaIndex;
                            be.Round = c + 1;
                            list.Add(be);
                        }
                    }
                }

                return list;
            }

            /// <summary>
            /// Updates the item list for all item combo boxes.
            /// </summary>
            public void SetItemList(List<string> items)
            {
                itemList = items ?? new List<string>();
                foreach (var combo in itemCombos)
                {
                    var current = combo.SelectedItem as string;
                    combo.Items.Clear();
                    combo.Items.Add("");
                    foreach (var item in itemList)
                        combo.Items.Add(item);
                    if (!string.IsNullOrEmpty(current) && combo.Items.Contains(current))
                        combo.SelectedItem = current;
                }
            }

            /// <summary>
            /// Adds an enemy to the grid from a Pet object.
            /// </summary>
            public void AddEnemyFromPet(Pet pet)
            {
                int vIdx = versions.IndexOf(pet.Version);
                if (vIdx < 0) return;

                int col = enemiesByVersion[vIdx].FindIndex(b => b == null);
                if (col == -1) col = enemiesByVersion[vIdx].Count;
                if (col == columnCount) AddColumn();
                while (enemiesByVersion[vIdx].Count <= col) enemiesByVersion[vIdx].Add(null);

                var be = CreateBattleEnemyFromPet(pet, areaIndex, col + 1);
                enemiesByVersion[vIdx][col] = be;
                PlaceEnemy(be, vIdx, col);
            }

            /// <summary>
            /// Removes an enemy and shifts the row left.
            /// </summary>
            private void RemoveEnemyAndShiftLeft(int vIdx, int col)
            {
                if (vIdx < 0 || vIdx >= enemiesByVersion.Count) return;
                if (col < 0 || col >= enemiesByVersion[vIdx].Count) return;

                enemiesByVersion[vIdx][col] = null;

                for (int c = col + 1; c < enemiesByVersion[vIdx].Count; c++)
                {
                    enemiesByVersion[vIdx][c - 1] = enemiesByVersion[vIdx][c];
                }
                if (enemiesByVersion[vIdx].Count > 0)
                    enemiesByVersion[vIdx][enemiesByVersion[vIdx].Count - 1] = null;

                RedrawEnemiesRow(vIdx);
            }

            /// <summary>
            /// Redraws the row of enemies for a version.
            /// </summary>
            private void RedrawEnemiesRow(int vIdx)
            {
                for (int c = 0; c < columnCount; c++)
                {
                    var cell = grid.GetControlFromPosition(c, vIdx + 1);
                    if (cell != null) grid.Controls.Remove(cell);
                }
                for (int c = 0; c < enemiesByVersion[vIdx].Count; c++)
                {
                    var be = enemiesByVersion[vIdx][c];
                    if (be != null)
                        PlaceEnemy(be, vIdx, c);
                }
            }
        }

        #endregion
    }
}
