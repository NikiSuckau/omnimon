using OmnimonModuleEditor.Controls;
using OmnimonModuleEditor.Models;
using OmnimonModuleEditor.Properties;
using OmnimonModuleEditor.Utils;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnimonModuleEditor
{
    /// <summary>
    /// Editor window for managing pet evolutions visually.
    /// /// </summary>
    public partial class EvolutionsEditorForm : Form
    {
        // Fields
        private List<Pet> pets;
        private string modulePath;
        private Module module;
        private ComboBox cmbVersions;
        private Button btnOrganize;
        private Button btnSave;
        private Button btnCancel;

        private Panel panelTop;
        private Panel panelLeft;
        private Panel panelRight;
        private Panel panelChart;

        private Panel draggedPanel;
        private Point dragOffset;

        private Panel draggingPanel = null;
        private Point dragStartPoint;

        private bool connectMode = false;
        private Button btnToggleConnect;
        private Panel selectedForConnection = null;

        private bool deleteMode = false;
        private Button btnDelete;

        private List<Connection> connections = new List<Connection>();
        private List<Item> items;
        private static readonly Random rand = new Random();
        private PetListPanel petListPanel;

        /// <summary>
        /// Initializes a new instance of the <see cref="EvolutionsEditorForm"/> class.
        /// </summary>
        public EvolutionsEditorForm(List<Pet> pets, string modulePath, Module module)
        {
            this.pets = pets;
            this.modulePath = modulePath;
            this.module = module;
            InitializeLayout();
            LoadDigimonsForSelectedVersion();
            LoadItemsFromJson();
        }

        #region Layout and UI Initialization

        /// <summary>
        /// Initializes the layout and UI controls.
        /// </summary>
        private void InitializeLayout()
        {
            this.Text = "Evolution EdiTor";
            this.Size = new Size(1200, 800);

            // Top bar with controls
            var flowTop = new FlowLayoutPanel
            {
                Dock = DockStyle.Top,
                Height = 50,
                Padding = new Padding(8),
                BackColor = SystemColors.Control,
                FlowDirection = FlowDirection.LeftToRight,
                AutoSize = false,
                WrapContents = false
            };

            flowTop.Controls.Add(new Label
            {
                Text = Resources.Label_Version,
                AutoSize = true,
                TextAlign = ContentAlignment.MiddleLeft,
                Margin = new Padding(0, 12, 4, 0)
            });

            cmbVersions = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Width = 120,
                Margin = new Padding(0, 8, 8, 0)
            };
            var versions = pets.Select(p => p.Version).Distinct().OrderBy(v => v).ToArray();
            foreach (var v in versions)
                cmbVersions.Items.Add(string.Format(Resources.Label_VersionWithNumber, v));
            if (cmbVersions.Items.Count > 0)
                cmbVersions.SelectedIndex = 0;
            flowTop.Controls.Add(cmbVersions);

            btnOrganize = new Button { Text = Resources.Button_Organize, Width = 90, Margin = new Padding(8, 8, 0, 0) };
            btnSave = new Button { Text = Resources.Button_Save, Width = 90, Margin = new Padding(8, 8, 0, 0) };
            btnCancel = new Button { Text = Resources.Button_Cancel, Width = 90, Margin = new Padding(8, 8, 0, 0) };

            flowTop.Controls.Add(btnOrganize);
            flowTop.Controls.Add(btnSave);
            flowTop.Controls.Add(btnCancel);

            btnToggleConnect = new Button
            {
                Text = Resources.Button_ToggleConnect,
                Width = 120,
                Margin = new Padding(8, 8, 0, 0),
                BackColor = Color.LightGray
            };
            btnToggleConnect.Click += BtnToggleConnect_Click;
            flowTop.Controls.Add(btnToggleConnect);

            btnDelete = new Button
            {
                Text = Resources.Button_Delete,
                Width = 90,
                Margin = new Padding(8, 8, 0, 0),
                BackColor = Color.LightGray
            };
            btnDelete.Click += BtnDelete_Click;
            flowTop.Controls.Add(btnDelete);

            panelTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                Padding = new Padding(0),
                BackColor = SystemColors.Control
            };
            panelTop.Controls.Add(flowTop);

            // Pet list panel (left)
            petListPanel = new PetListPanel
            {
                Dock = DockStyle.Left,
                Width = 230,
                Padding = new Padding(4),
                BackColor = Color.WhiteSmoke
            };

            LoadPetListPanel();

            // Left panel (hidden, kept for compatibility)
            panelLeft = new Panel
            {
                Dock = DockStyle.Left,
                Width = 0,
                Padding = new Padding(0),
                BackColor = Color.WhiteSmoke
            };

            // Right panel (canvas)
            panelRight = new Panel
            {
                Dock = DockStyle.Fill,
                Padding = new Padding(4),
                BackColor = Color.White
            };

            panelChart = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = ColorTranslator.FromHtml("#757575"),
                AutoScroll = true
            };
            panelRight.Controls.Add(panelChart);

            // Add controls to form
            this.Controls.Add(panelRight);
            this.Controls.Add(petListPanel);
            this.Controls.Add(panelTop);

            // Events
            cmbVersions.SelectedIndexChanged += (s, e) =>
            {
                LoadPetListPanel();
                LoadDigimonsForSelectedVersion();
                BuildEvolutionTree();
            };
            btnCancel.Click += (s, e) => this.DialogResult = DialogResult.Cancel;

            panelChart.AllowDrop = true;
            panelChart.DragEnter += PanelChart_DragEnter;
            panelChart.DragDrop += PanelChart_DragDrop;
            panelChart.Paint += PanelChart_Paint;
            panelChart.MouseClick += PanelChart_MouseClick;

            btnOrganize.Click += BtnOrganize_Click;

            btnSave.Click += (s, e) =>
            {
                SaveEvolutionTree();
                this.DialogResult = DialogResult.OK;
            };

            AddStage0PetToCanvas();
            BuildEvolutionTree();
        }

        #endregion

        #region Pet List and Canvas Population

        /// <summary>
        /// Populates the pet list panel with pets from the selected version.
        /// </summary>
        private void LoadPetListPanel()
        {
            petListPanel.PanelPetList.Controls.Clear();
            if (cmbVersions.SelectedIndex < 0) return;

            var selectedVersion = int.Parse(cmbVersions.SelectedItem.ToString().Replace(Resources.Label_Version + " ", ""));
            var digimons = pets.Where(p => p.Version == selectedVersion).OrderBy(p => p.Stage).ThenBy(p => p.Name).ToList();

            int y = 8;
            foreach (var pet in digimons)
            {
                var petPanel = CreatePetPanel(pet, false);
                petPanel.Location = new Point(8, y);
                petPanel.Cursor = Cursors.Hand;
                petPanel.MouseDown += PetPanel_MouseDown;
                petListPanel.PanelPetList.Controls.Add(petPanel);
                y += petPanel.Height + 8;
            }
        }

        /// <summary>
        /// Loads the pet list for the selected version (legacy, kept for compatibility).
        /// </summary>
        private void LoadDigimonsForSelectedVersion()
        {
            petListPanel.PanelPetList.Controls.Clear();
            if (cmbVersions.SelectedIndex < 0) return;

            var selectedVersion = int.Parse(cmbVersions.SelectedItem.ToString().Replace(Resources.Label_Version + " ", ""));
            var digimons = pets.Where(p => p.Version == selectedVersion).OrderBy(p => p.Stage).ThenBy(p => p.Name).ToList();

            int y = 8;
            foreach (var pet in digimons)
            {
                var petPanel = CreatePetPanel(pet);
                petPanel.Location = new Point(8, y);
                petPanel.Cursor = Cursors.Hand;
                petPanel.MouseDown += PetPanel_MouseDown;
                petListPanel.PanelPetList.Controls.Add(petPanel);
                y += petPanel.Height + 8;
            }
        }

        /// <summary>
        /// Adds the root pet and its evolutions to the canvas.
        /// </summary>
        private void AddStage0PetToCanvas()
        {
            BuildEvolutionTree();
        }

        /// <summary>
        /// Builds the evolution tree on the canvas for the selected version.
        /// </summary>
        private void BuildEvolutionTree()
        {
            panelChart.Controls.Clear();
            foreach (var conn in connections)
                if (conn.CriteriaPanel != null)
                    panelChart.Controls.Remove(conn.CriteriaPanel);
            connections.Clear();

            if (cmbVersions.SelectedIndex < 0) return;
            int selectedVersion = int.Parse(cmbVersions.SelectedItem.ToString().Replace(Resources.Label_Version + " ", ""));
            var rootPets = pets.Where(p => p.Version == selectedVersion && p.Stage == 0).ToList();
            if (rootPets.Count == 0) return;

            var petToPanel = new Dictionary<Pet, Panel>();
            int startX = 60, startY = 60;
            int spacingX = 320;
            for (int i = 0; i < rootPets.Count; i++)
            {
                int x = startX + i * spacingX;
                AddPetAndEvolutionsRecursive(rootPets[i], x, startY, 0, petToPanel);
            }
            UpdateCanvasScroll();
            panelChart.Invalidate();
        }

        /// <summary>
        /// Recursively adds a pet and its evolutions to the canvas.
        /// </summary>
        private void AddPetAndEvolutionsRecursive(Pet pet, int x, int y, int depth, Dictionary<Pet, Panel> petToPanel)
        {
            if (petToPanel.ContainsKey(pet))
                return;

            var petPanel = CreatePetPanel(pet, true);
            petPanel.Location = new Point(x, y);
            panelChart.Controls.Add(petPanel);
            petPanel.BringToFront();
            petToPanel[pet] = petPanel;

            if (pet.Evolve == null || pet.Evolve.Count == 0)
                return;

            int spacingX = 320;
            int spacingY = 200;
            int count = pet.Evolve.Count;
            int childX0 = x - ((count - 1) * spacingX) / 2;

            for (int i = 0; i < count; i++)
            {
                var evo = pet.Evolve[i];
                var childPet = pets.FirstOrDefault(p => p.Name == evo.To && p.Version == pet.Version);
                if (childPet == null) continue;

                int childX = childX0 + i * spacingX;
                int childY = y + spacingY;

                AddPetAndEvolutionsRecursive(childPet, childX, childY, depth + 1, petToPanel);

                var childPanel = petToPanel[childPet];
                var conn = new Connection(petPanel, childPanel, GetRandomLineColor());
                conn.CriteriaPanel = CreateCriteriaPanel(evo);
                panelChart.Controls.Add(conn.CriteriaPanel);
                conn.CriteriaPanel.BringToFront();
                connections.Add(conn);
            }
        }

        #endregion

        #region Pet Panel Creation and Attribute Helpers

        /// <summary>
        /// Creates a panel representing a pet, for either the list or the canvas.
        /// </summary>
        private Panel CreatePetPanel(Pet pet, bool forCanvas = false)
        {
            var itemPanel = new Panel
            {
                Size = new Size(190, 56),
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.White,
                Tag = pet
            };

            PictureBox pb = new PictureBox
            {
                Location = new Point(4, 4),
                Size = new Size(48, 48),
                SizeMode = PictureBoxSizeMode.Zoom,
                BackColor = GetAttributeColor(pet.Attribute ?? ""),
                BorderStyle = BorderStyle.FixedSingle
            };

            // Use new sprite loading system
            var sprite = SpriteUtils.LoadSingleSprite(pet.Name, modulePath, PetUtils.FixedNameFormat);
            pb.Image = sprite;

            itemPanel.Controls.Add(pb);

            Label lblName = new Label
            {
                Text = pet.Name,
                Location = new Point(60, 4),
                AutoSize = true,
                Font = new Font(FontFamily.GenericSansSerif, 11, FontStyle.Bold),
                ForeColor = Color.DeepSkyBlue
            };
            itemPanel.Controls.Add(lblName);

            Label lblInfo = new Label
            {
                Text = string.Format(Resources.Label_VersionStage, pet.Version, pet.Stage),
                Location = new Point(60, 28),
                AutoSize = true,
                Font = new Font(FontFamily.GenericSansSerif, 8, FontStyle.Regular),
                ForeColor = Color.DeepSkyBlue
            };
            itemPanel.Controls.Add(lblInfo);

            if (forCanvas)
            {
                itemPanel.MouseDown += PetPanel_MouseDown;
                itemPanel.MouseMove += PetPanel_MouseMove;
                itemPanel.MouseUp += PetPanel_MouseUp;
                itemPanel.Click += PetPanel_ClickForConnection;
                itemPanel.Click += PetPanel_ClickForDelete;
            }

            return itemPanel;
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

        /// <summary>
        /// Gets a random color for evolution lines.
        /// </summary>
        private Color GetRandomLineColor()
        {
            return Color.FromArgb(255, rand.Next(32, 224), rand.Next(32, 224), rand.Next(32, 224));
        }

        #endregion

        #region Drag and Drop, Mouse, and Canvas Events

        /// <summary>
        /// Handles mouse down for pet panels (drag from list or move in canvas).
        /// </summary>
        private void PetPanel_MouseDown(object sender, MouseEventArgs e)
        {
            if (sender is Panel panel && e.Button == MouseButtons.Left)
            {
                if (panel.Parent == petListPanel.PanelPetList)
                {
                    if (panel.Tag is Pet pet)
                    {
                        string data = $"{pet.Name}|{pet.Version}";
                        panel.DoDragDrop(data, DragDropEffects.Copy);
                    }
                }
                else if (panel.Parent == panelChart)
                {
                    draggingPanel = panel;
                    dragStartPoint = e.Location;
                    panel.BringToFront();
                }
            }
        }

        private void PetPanel_MouseMove(object sender, MouseEventArgs e)
        {
            if (draggingPanel != null && e.Button == MouseButtons.Left)
            {
                var newLocation = draggingPanel.Location;
                newLocation.Offset(e.X - dragStartPoint.X, e.Y - dragStartPoint.Y);
                newLocation.X = Math.Max(0, Math.Min(panelChart.AutoScrollMinSize.Width - draggingPanel.Width, newLocation.X));
                newLocation.Y = Math.Max(0, Math.Min(panelChart.AutoScrollMinSize.Height - draggingPanel.Height, newLocation.Y));
                draggingPanel.Location = newLocation;
                panelChart.Invalidate();
                UpdateCanvasScroll();
                UpdateCriteriaPanels();
            }
        }

        private void PetPanel_MouseUp(object sender, MouseEventArgs e)
        {
            draggingPanel = null;
        }

        private void DraggedPanel_MouseMove(object sender, MouseEventArgs e)
        {
            if (draggedPanel != null && e.Button == MouseButtons.Left)
            {
                var mousePos = panelChart.PointToClient(Cursor.Position);
                draggedPanel.Location = new Point(mousePos.X - dragOffset.X, mousePos.Y - dragOffset.Y);
            }
        }

        private void DraggedPanel_MouseUp(object sender, MouseEventArgs e)
        {
            if (draggedPanel != null)
            {
                draggedPanel.MouseMove -= DraggedPanel_MouseMove;
                draggedPanel.MouseUp -= DraggedPanel_MouseUp;
                draggedPanel = null;
            }
        }

        private void PanelChart_DragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.StringFormat))
                e.Effect = DragDropEffects.Copy;
            else
                e.Effect = DragDropEffects.None;
        }

        private void PanelChart_DragDrop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.StringFormat))
            {
                string data = (string)e.Data.GetData(DataFormats.StringFormat);
                var parts = data.Split('|');
                if (parts.Length == 2)
                {
                    string name = parts[0];
                    int version;
                    if (int.TryParse(parts[1], out version))
                    {
                        var pet = pets.FirstOrDefault(p => p.Name == name && p.Version == version);
                        if (pet != null)
                        {
                            var clientPoint = panelChart.PointToClient(new Point(e.X, e.Y));
                            var petPanel = CreatePetPanel(pet, true);
                            petPanel.Location = clientPoint;
                            panelChart.Controls.Add(petPanel);
                            petPanel.BringToFront();
                            UpdateCanvasScroll();
                        }
                    }
                }
            }
        }

        private void PanelChart_Paint(object sender, PaintEventArgs e)
        {
            foreach (var conn in connections)
            {
                if (conn.From.Parent != panelChart || conn.To.Parent != panelChart)
                    continue;

                var p1 = conn.From;
                var p2 = conn.To;
                Point c1 = new Point(p1.Left + p1.Width / 2, p1.Top + p1.Height / 2);
                Point c2 = new Point(p2.Left + p2.Width / 2, p2.Top + p2.Height / 2);

                using (var pen = new Pen(conn.LineColor, 3))
                {
                    pen.CustomEndCap = new AdjustableArrowCap(8, 10, true);
                    e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
                    e.Graphics.DrawLine(pen, c1, c2);
                }
            }
            UpdateCriteriaPanels();
        }

        private void PanelChart_MouseClick(object sender, MouseEventArgs e)
        {
            if (!deleteMode) return;

            const int hitTestRadius = 6;
            Connection toRemove = null;
            foreach (var conn in connections)
            {
                if (conn.From.Parent != panelChart || conn.To.Parent != panelChart)
                    continue;

                var p1 = conn.From;
                var p2 = conn.To;
                Point c1 = new Point(p1.Left + p1.Width / 2, p1.Top + p1.Height / 2);
                Point c2 = new Point(p2.Left + p2.Width / 2, p2.Top + p2.Height / 2);

                float dist = DistancePointToSegment(e.Location, c1, c2);
                if (dist <= hitTestRadius)
                {
                    toRemove = conn;
                    break;
                }
            }

            if (toRemove != null)
            {
                if (toRemove.CriteriaPanel != null)
                    panelChart.Controls.Remove(toRemove.CriteriaPanel);
                connections.Remove(toRemove);
                panelChart.Invalidate();
                deleteMode = false;
                btnDelete.BackColor = Color.LightGray;
                panelChart.Cursor = connectMode ? Cursors.Cross : Cursors.Default;
                return;
            }
        }

        #endregion

        #region Evolution Connections and Criteria

        /// <summary>
        /// Handles the connect mode toggle button click.
        /// </summary>
        private void BtnToggleConnect_Click(object sender, EventArgs e)
        {
            connectMode = !connectMode;
            btnToggleConnect.BackColor = connectMode ? Color.LightGreen : Color.LightGray;
            selectedForConnection = null;
            panelChart.Cursor = connectMode ? Cursors.Cross : Cursors.Default;
        }

        /// <summary>
        /// Handles click for connecting two pet panels.
        /// </summary>
        private void PetPanel_ClickForConnection(object sender, EventArgs e)
        {
            if (!connectMode) return;
            if (!(sender is Panel panel)) return;

            if (selectedForConnection == null)
            {
                selectedForConnection = panel;
                panel.BackColor = Color.LightBlue;
            }
            else if (selectedForConnection != panel)
            {
                var fromPet = (Pet)selectedForConnection.Tag;
                var toPet = (Pet)panel.Tag;
                var evo = new Evolution { To = toPet.Name };
                var conn = new Connection(selectedForConnection, panel, GetRandomLineColor());
                conn.CriteriaPanel = CreateCriteriaPanel(evo);
                panelChart.Controls.Add(conn.CriteriaPanel);
                conn.CriteriaPanel.BringToFront();
                connections.Add(conn);
                selectedForConnection.BackColor = Color.White;
                selectedForConnection = null;
                panelChart.Invalidate();
                UpdateCriteriaPanels();
            }
        }

        /// <summary>
        /// Handles click for deleting a pet panel and its connections.
        /// </summary>
        private void PetPanel_ClickForDelete(object sender, EventArgs e)
        {
            if (!deleteMode) return;
            if (!(sender is Panel panel)) return;

            var toRemove = connections.Where(conn => conn.From == panel || conn.To == panel).ToList();
            foreach (var conn in toRemove)
            {
                if (conn.CriteriaPanel != null)
                    panelChart.Controls.Remove(conn.CriteriaPanel);
                connections.Remove(conn);
            }

            panelChart.Controls.Remove(panel);
            panelChart.Invalidate();
            deleteMode = false;
            btnDelete.BackColor = Color.LightGray;
            panelChart.Cursor = connectMode ? Cursors.Cross : Cursors.Default;
            UpdateCanvasScroll();
        }

        /// <summary>
        /// Updates the position of criteria panels for all connections.
        /// </summary>
        private void UpdateCriteriaPanels()
        {
            var grouped = connections
                .Where(c => c.CriteriaPanel != null && c.From.Parent == panelChart && c.To.Parent == panelChart)
                .GroupBy(c => new { From = c.From, To = c.To })
                .ToList();

            foreach (var group in grouped)
            {
                var connList = group.ToList();
                int n = connList.Count;
                if (n == 1)
                {
                    var conn = connList[0];
                    var p1 = conn.From;
                    var p2 = conn.To;
                    Point c1 = new Point(p1.Left + p1.Width / 2, p1.Top + p1.Height / 2);
                    Point c2 = new Point(p2.Left + p2.Width / 2, p2.Top + p2.Height / 2);
                    int x = (c1.X + c2.X) / 2 - conn.CriteriaPanel.Width / 2;
                    int y = (c1.Y + c2.Y) / 2 - conn.CriteriaPanel.Height / 2;
                    conn.CriteriaPanel.Location = new Point(x, y);
                    conn.CriteriaPanel.BringToFront();
                }
                else
                {
                    var p1 = group.Key.From;
                    var p2 = group.Key.To;
                    Point c1 = new Point(p1.Left + p1.Width / 2, p1.Top + p1.Height / 2);
                    Point c2 = new Point(p2.Left + p2.Width / 2, p2.Top + p2.Height / 2);
                    int centerX = (c1.X + c2.X) / 2;
                    int centerY = (c1.Y + c2.Y) / 2;
                    int totalWidth = connList.Sum(c => c.CriteriaPanel.Width) + (n - 1) * 8;
                    int startX = centerX - totalWidth / 2;
                    for (int i = 0; i < n; i++)
                    {
                        var panel = connList[i].CriteriaPanel;
                        int x = startX;
                        int y = centerY - panel.Height / 2;
                        panel.Location = new Point(x, y);
                        panel.BringToFront();
                        startX += panel.Width + 8;
                    }
                }
            }
        }

        /// <summary>
        /// Creates a panel displaying evolution criteria.
        /// </summary>
        private Panel CreateCriteriaPanel(Evolution evo)
        {
            var panel = new Panel
            {
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                BackColor = Color.White,
                BorderStyle = BorderStyle.FixedSingle,
                Padding = new Padding(4)
            };

            var font = new Font(FontFamily.GenericSansSerif, 7, FontStyle.Regular);
            var lines = new List<string>();

            Func<IEnumerable<int>, string> formatRange = arr =>
                string.Join(",", arr.Select(v => v == 999999 ? "+" : v.ToString()));

            if (evo != null)
            {
                if (evo.ConditionHearts != null) lines.Add($"Condition Hearts: {formatRange(evo.ConditionHearts)}");
                if (evo.Training != null) lines.Add($"Training: {formatRange(evo.Training)}");
                if (evo.Battles != null) lines.Add($"Battles: {formatRange(evo.Battles)}");
                if (evo.WinRatio != null) lines.Add($"Win Ratio: {formatRange(evo.WinRatio)}");
                if (evo.WinCount != null) lines.Add($"Win Count: {formatRange(evo.WinCount)}"); // New field
                if (evo.Mistakes != null) lines.Add($"Mistakes: {formatRange(evo.Mistakes)}");
                if (evo.Level != null) lines.Add($"Level: {formatRange(evo.Level)}");
                if (evo.Overfeed != null) lines.Add($"Overfeed: {formatRange(evo.Overfeed)}");
                if (evo.SleepDisturbances != null) lines.Add($"Sleep Disturbances: {formatRange(evo.SleepDisturbances)}");
                if (evo.Area != null) lines.Add($"Area: {(evo.Area == 999999 ? "+" : evo.Area.ToString())}");
                if (evo.Stage != null) lines.Add($"Stage: {(evo.Stage == 999999 ? "+" : evo.Stage.ToString())}");
                if (evo.Version != null) lines.Add($"Version: {(evo.Version == 999999 ? "+" : evo.Version.ToString())}");
                if (!string.IsNullOrEmpty(evo.Attribute)) lines.Add($"Attribute: {evo.Attribute}");
                if (!string.IsNullOrEmpty(evo.Jogress)) lines.Add($"Jogress: {evo.Jogress}");
                if (evo.JogressPrefix != null) lines.Add($"Jogress Prefix: {(evo.JogressPrefix.Value ? "Yes" : "No")}");
                if (evo.SpecialEncounter != null) lines.Add($"Special Encounter: {evo.SpecialEncounter}");
                if (evo.Stage5 != null) lines.Add($"Stage-5: {formatRange(evo.Stage5)}");
                if (evo.Stage6 != null) lines.Add($"Stage-6: {formatRange(evo.Stage6)}"); // New field
                if (evo.Stage7 != null) lines.Add($"Stage-7: {formatRange(evo.Stage7)}"); // New field
                if (evo.Stage8 != null) lines.Add($"Stage-8: {formatRange(evo.Stage8)}"); // New field
                if (evo.Item != null) lines.Add($"Item: {evo.Item}");
                if (evo.TimeRange != null && (evo.TimeRange.Length > 0 && (!string.IsNullOrWhiteSpace(evo.TimeRange[0]) || (evo.TimeRange.Length > 1 && !string.IsNullOrWhiteSpace(evo.TimeRange[1])))))
                {
                    string t0 = evo.TimeRange.Length > 0 ? evo.TimeRange[0] : "";
                    string t1 = evo.TimeRange.Length > 1 ? evo.TimeRange[1] : "";
                    if (t0.Replace(":","").Trim().Length > 0 && t1.Replace(":", "").Trim().Length > 0)
                        lines.Add($"Time Range: {t0} - {t1}");
                }
                if (evo.Trophies != null) lines.Add($"Trophies: {formatRange(evo.Trophies)}"); // New field
                if (evo.VitalValues != null) lines.Add($"Vital Values: {formatRange(evo.VitalValues)}"); // New field
                if (evo.Weigth != null) lines.Add($"Weight: {formatRange(evo.Weigth)}"); // New field
                if (evo.QuestsCompleted != null) lines.Add($"Quests Completed: {formatRange(evo.QuestsCompleted)}"); // New field
                if (evo.Pvp != null) lines.Add($"PVP: {formatRange(evo.Pvp)}"); // New field
            }

            // Define the click event handler that opens the EvolutionCriteriaForm
            EventHandler clickHandler = (s, e) =>
            {
                using (var form = new EvolutionCriteriaForm(evo, this.items))
                {
                    if (form.ShowDialog(this) == DialogResult.OK)
                    {
                        var parent = panel.Parent;
                        int idx = parent?.Controls.IndexOf(panel) ?? -1;
                        var newPanel = CreateCriteriaPanel(evo);
                        if (parent != null && idx >= 0)
                        {
                            parent.Controls.Remove(panel);
                            parent.Controls.Add(newPanel);
                            newPanel.BringToFront();
                        }
                        var conn = connections.FirstOrDefault(c => c.CriteriaPanel == panel);
                        if (conn != null)
                            conn.CriteriaPanel = newPanel;
                        UpdateCriteriaPanels();
                    }
                }
            };

            Label label;
            if (lines.Count == 0)
            {
                label = new Label
                {
                    Text = "no criteria",
                    Dock = DockStyle.Fill,
                    TextAlign = ContentAlignment.MiddleCenter,
                    ForeColor = Color.Gray,
                    Font = font,
                    AutoSize = true,
                    Cursor = Cursors.Hand
                };
                panel.Controls.Add(label);
            }
            else
            {
                label = new Label
                {
                    Text = string.Join(Environment.NewLine, lines),
                    Dock = DockStyle.Fill,
                    TextAlign = ContentAlignment.TopLeft,
                    ForeColor = Color.Black,
                    Font = font,
                    AutoSize = true,
                    Cursor = Cursors.Hand
                };
                panel.Controls.Add(label);
            }

            panel.Tag = evo;
            panel.Cursor = Cursors.Hand;

            // Add the same click event to both the panel and the label
            panel.Click += clickHandler;
            label.Click += clickHandler;

            return panel;
        }

        #endregion

        #region Utility and Save Methods

        /// <summary>
        /// Updates the scrollable area of the canvas based on content.
        /// </summary>
        private void UpdateCanvasScroll()
        {
            int maxX = 0, maxY = 0;
            int minX = int.MaxValue, minY = int.MaxValue;
            foreach (Control ctrl in panelChart.Controls)
            {
                if (ctrl is Panel p)
                {
                    maxX = Math.Max(maxX, p.Right);
                    maxY = Math.Max(maxY, p.Bottom);
                    minX = Math.Min(minX, p.Left);
                    minY = Math.Min(minY, p.Top);
                }
            }

            int minWidth = 2400;
            int minHeight = 1600;
            int contentWidth = maxX + 40;
            int contentHeight = maxY + 40;
            bool needsExpand = minX < 40 || minY < 40 || maxX > panelChart.AutoScrollMinSize.Width - 80 || maxY > panelChart.AutoScrollMinSize.Height - 80;

            int newWidth = Math.Max(minWidth, contentWidth);
            int newHeight = Math.Max(minHeight, contentHeight);

            if (needsExpand)
            {
                newWidth = Math.Max(newWidth, panelChart.AutoScrollMinSize.Width * 2);
                newHeight = Math.Max(newHeight, panelChart.AutoScrollMinSize.Height * 2);
            }

            panelChart.AutoScrollMinSize = new Size(newWidth, newHeight);
        }

        /// <summary>
        /// Organizes the pet panels on the canvas by stage.
        /// </summary>
        private void BtnOrganize_Click(object sender, EventArgs e)
        {
            var panelsByStage = new Dictionary<int, List<Panel>>();
            var petByPanel = new Dictionary<Panel, Pet>();
            foreach (Control ctrl in panelChart.Controls)
            {
                if (ctrl is Panel p && p.Tag is Pet pet)
                {
                    int stage = Math.Max(0, Math.Min(8, pet.Stage));
                    if (!panelsByStage.ContainsKey(stage))
                        panelsByStage[stage] = new List<Panel>();
                    panelsByStage[stage].Add(p);
                    petByPanel[p] = pet;
                }
            }

            int rowHeight = 150;
            int panelSpacing = 30;
            int panelWidth = 190;
            int marginLeft = 40;
            var prevStagePanelCenters = new Dictionary<Pet, int>();

            for (int stage = 0; stage <= 8; stage++)
            {
                if (!panelsByStage.ContainsKey(stage)) continue;
                var list = panelsByStage[stage];

                if (stage > 0 && panelsByStage.ContainsKey(stage - 1))
                {
                    var parentPanels = panelsByStage[stage - 1];
                    var parentPets = parentPanels.Select(p => petByPanel[p]).ToList();

                    var petToParentCenters = new Dictionary<Panel, double>();
                    foreach (var panel in list)
                    {
                        var pet = petByPanel[panel];
                        var parentXs = parentPets
                            .Where(parent => parent.Evolve != null && parent.Evolve.Any(evo => evo.To == pet.Name))
                            .Select(parent =>
                            {
                                var parentPanel = parentPanels.FirstOrDefault(pp => petByPanel[pp] == parent);
                                return parentPanel != null ? parentPanel.Left + parentPanel.Width / 2 : (int?)null;
                            })
                            .Where(x => x.HasValue)
                            .Select(x => x.Value)
                            .ToList();

                        double avgX = parentXs.Count > 0 ? parentXs.Average() : 0;
                        petToParentCenters[panel] = avgX;
                    }

                    list.Sort((a, b) => petToParentCenters[a].CompareTo(petToParentCenters[b]));
                }

                int count = list.Count;
                int totalWidth = count * panelWidth + (count - 1) * panelSpacing;
                int startX = Math.Max(marginLeft, (panelChart.Width - totalWidth) / 2);

                for (int i = 0; i < count; i++)
                {
                    var p = list[i];
                    int x = startX + i * (panelWidth + panelSpacing);
                    int y = 40 + stage * rowHeight;
                    p.Location = new Point(x, y);
                    prevStagePanelCenters[petByPanel[p]] = x + panelWidth / 2;
                }
            }
            panelChart.Invalidate();
            UpdateCanvasScroll();
        }

        /// <summary>
        /// Utility function for point-to-line distance.
        /// </summary>
        private float DistancePointToSegment(Point pt, Point p1, Point p2)
        {
            float dx = p2.X - p1.X;
            float dy = p2.Y - p1.Y;
            if (dx == 0 && dy == 0)
                return (float)Math.Sqrt((pt.X - p1.X) * (pt.X - p1.X) + (pt.Y - p1.Y) * (pt.Y - p1.Y));
            float t = ((pt.X - p1.X) * dx + (pt.Y - p1.Y) * dy) / (dx * dx + dy * dy);
            t = Math.Max(0, Math.Min(1, t));
            float projX = p1.X + t * dx;
            float projY = p1.Y + t * dy;
            return (float)Math.Sqrt((pt.X - projX) * (pt.X - projX) + (pt.Y - projY) * (pt.Y - projY));
        }

        /// <summary>
        /// Saves the current evolution tree to the pet objects.
        /// </summary>
        private void SaveEvolutionTree()
        {
            if (cmbVersions.SelectedIndex < 0) return;
            int selectedVersion = int.Parse(cmbVersions.SelectedItem.ToString().Replace(Resources.Label_Version + " ", ""));
            var petsInCanvas = panelChart.Controls.OfType<Panel>()
                .Where(p => p.Tag is Pet pet && pet.Version == selectedVersion)
                .Select(p => (Pet)p.Tag)
                .ToList();

            foreach (var pet in petsInCanvas)
                pet.Evolve = new List<Evolution>();

            foreach (var conn in connections)
            {
                if (!(conn.From.Tag is Pet fromPet) || !(conn.To.Tag is Pet toPet))
                    continue;
                if (fromPet.Version != selectedVersion || toPet.Version != selectedVersion)
                    continue;

                Evolution evo = null;
                if (conn.CriteriaPanel != null && conn.CriteriaPanel.Tag is Evolution taggedEvo)
                {
                    evo = taggedEvo;
                }
                else
                {
                    evo = fromPet.Evolve?.FirstOrDefault(e => e.To == toPet.Name);
                }

                if (evo == null)
                    evo = new Evolution { To = toPet.Name };

                fromPet.Evolve.Add(CloneEvolution(evo));
            }
        }

        /// <summary>
        /// Utility function to copy all fields of Evolution.
        /// </summary>
        private Evolution CloneEvolution(Evolution evo)
        {
            return new Evolution
            {
                To = evo.To,
                ConditionHearts = evo.ConditionHearts != null ? (int[])evo.ConditionHearts.Clone() : null,
                Training = evo.Training != null ? (int[])evo.Training.Clone() : null,
                Battles = evo.Battles != null ? (int[])evo.Battles.Clone() : null,
                WinRatio = evo.WinRatio != null ? (int[])evo.WinRatio.Clone() : null,
                WinCount = evo.WinCount != null ? (int[])evo.WinCount.Clone() : null, // New field
                Mistakes = evo.Mistakes != null ? (int[])evo.Mistakes.Clone() : null,
                Level = evo.Level != null ? (int[])evo.Level.Clone() : null,
                Overfeed = evo.Overfeed != null ? (int[])evo.Overfeed.Clone() : null,
                SleepDisturbances = evo.SleepDisturbances != null ? (int[])evo.SleepDisturbances.Clone() : null,
                Area = evo.Area,
                Stage = evo.Stage,
                Version = evo.Version,
                Attribute = evo.Attribute,
                Jogress = evo.Jogress,
                JogressPrefix = evo.JogressPrefix, // <-- Adicionado
                SpecialEncounter = evo.SpecialEncounter,
                Stage5 = evo.Stage5 != null ? (int[])evo.Stage5.Clone() : null,
                Stage6 = evo.Stage6 != null ? (int[])evo.Stage6.Clone() : null, // New field
                Stage7 = evo.Stage7 != null ? (int[])evo.Stage7.Clone() : null, // New field
                Stage8 = evo.Stage8 != null ? (int[])evo.Stage8.Clone() : null, // New field
                Item = evo.Item,
                TimeRange = evo.TimeRange != null ? (string[])evo.TimeRange.Clone() : null, // <-- Adicionado
                Trophies = evo.Trophies != null ? (int[])evo.Trophies.Clone() : null, // New field
                VitalValues = evo.VitalValues != null ? (int[])evo.VitalValues.Clone() : null, // New field
                Weigth = evo.Weigth != null ? (int[])evo.Weigth.Clone() : null, // New field
                QuestsCompleted = evo.QuestsCompleted != null ? (int[])evo.QuestsCompleted.Clone() : null, // New field
                Pvp = evo.Pvp != null ? (int[])evo.Pvp.Clone() : null // New field
            };
        }

        /// <summary>
        /// Handles the delete mode toggle button click.
        /// </summary>
        private void BtnDelete_Click(object sender, EventArgs e)
        {
            deleteMode = !deleteMode;
            btnDelete.BackColor = deleteMode ? Color.Red : Color.LightGray;
            panelChart.Cursor = deleteMode ? Cursors.No : (connectMode ? Cursors.Cross : Cursors.Default);
        }

        /// <summary>
        /// Loads the items from the item.json file.
        /// </summary>
        private void LoadItemsFromJson()
        {
            this.items = new List<Item>();
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
                            this.items = JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText());
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error loading item.json: " + ex.Message);
                }
            }
        }

        #endregion

        #region Internal Classes

        /// <summary>
        /// Represents a visual connection (evolution) between two pet panels.
        /// </summary>
        private class Connection
        {
            public Panel From { get; }
            public Panel To { get; }
            public Color LineColor { get; }
            public Panel CriteriaPanel { get; set; }
            public Connection(Panel from, Panel to, Color color)
            {
                From = from;
                To = to;
                LineColor = color;
                CriteriaPanel = null;
            }
        }

        #endregion
    }
}
