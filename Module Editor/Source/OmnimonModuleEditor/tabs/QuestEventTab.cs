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
    /// Tab for managing and editing quests and events in the module.
    /// </summary>
    public partial class QuestEventTab : UserControl
    {
        private TabControl mainTabControl;
        private TabPage questTab;
        private TabPage eventTab;
        private QuestPanel questPanel;
        private EventPanel eventPanel;
        private string modulePath;
        private Module module;

        /// <summary>
        /// Initializes a new instance of the <see cref="QuestEventTab"/> class.
        /// </summary>
        public QuestEventTab()
        {
            InitializeComponent();
            this.Name = "QuestEventTab";
        }

        /// <summary>
        /// Sets the module context for this tab.
        /// </summary>
        public void SetModule(string modulePath, Module module)
        {
            this.modulePath = modulePath;
            this.module = module;
            questPanel.SetModule(modulePath, module);
            eventPanel.SetModule(modulePath, module);
        }

        /// <summary>
        /// Saves quests and events to their respective JSON files.
        /// </summary>
        public void Save()
        {
            questPanel?.Save();
            eventPanel?.Save();
        }

        #region Layout and UI Initialization

        /// <summary>
        /// Initializes the layout and UI controls.
        /// </summary>
        private void InitializeComponent()
        {
            this.Dock = DockStyle.Fill;

            mainTabControl = new TabControl
            {
                Dock = DockStyle.Fill
            };

            // Quests Tab
            questTab = new TabPage("Quests");
            questPanel = new QuestPanel();
            questPanel.Dock = DockStyle.Fill;
            questTab.Controls.Add(questPanel);

            // Events Tab
            eventTab = new TabPage("Events");
            eventPanel = new EventPanel();
            eventPanel.Dock = DockStyle.Fill;
            eventTab.Controls.Add(eventPanel);

            mainTabControl.TabPages.Add(questTab);
            mainTabControl.TabPages.Add(eventTab);

            this.Controls.Add(mainTabControl);
        }

        #endregion

        #region Internal Classes

        /// <summary>
        /// Panel for managing quests.
        /// </summary>
        private class QuestPanel : UserControl
        {
            private DataGridView dgvQuests;
            private BindingSource bindingSource;
            private Button btnAdd;
            private Button btnRemove;
            private List<Quest> quests = new List<Quest>();
            private string modulePath;
            private Module module;
            private List<Item> items = new List<Item>();
            private List<string> itemNames = new List<string>(); // Cache item names
            private bool isUpdatingCombos = false; // Prevent recursive updates

            public QuestPanel()
            {
                InitializeComponent();
            }

            public void SetModule(string modulePath, Module module)
            {
                this.modulePath = modulePath;
                this.module = module;
                LoadItemsFromJson();
                LoadQuestsFromJson();
            }

            public void Save()
            {
                if (string.IsNullOrEmpty(modulePath) || quests == null)
                    return;

                // Update quest names automatically
                UpdateQuestNames();

                string questPath = Path.Combine(modulePath, "quests.json");
                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
                };
                var obj = new { quests = quests };
                try
                {
                    string json = JsonSerializer.Serialize(obj, options);
                    File.WriteAllText(questPath, json);
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error saving quests.json: " + ex.Message);
                }
            }

            private void InitializeComponent()
            {
                this.Dock = DockStyle.Fill;

                var mainLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 2,
                    ColumnCount = 1,
                    Padding = new Padding(8),
                    BackColor = SystemColors.Control
                };
                mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
                mainLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));

                // Initialize BindingSource
                bindingSource = new BindingSource();

                dgvQuests = new DataGridView
                {
                    Dock = DockStyle.Fill,
                    AutoGenerateColumns = false,
                    AllowUserToAddRows = false,
                    AllowUserToDeleteRows = false,
                    RowHeadersVisible = false,
                    SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                    MultiSelect = false,
                    ReadOnly = false,
                    AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                    DataSource = bindingSource
                };

                // Name column (read-only, auto-generated)
                var colName = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Name",
                    HeaderText = "Name",
                    ReadOnly = true
                };
                dgvQuests.Columns.Add(colName);

                // Quest Type column
                var colQuestType = new DataGridViewComboBoxColumn
                {
                    DataPropertyName = "QuestType",
                    HeaderText = "Type",
                    DataSource = Enum.GetValues(typeof(QuestType)),
                    FlatStyle = FlatStyle.Flat
                };
                dgvQuests.Columns.Add(colQuestType);

                // Target Amount Range columns
                var colRangeMin = new DataGridViewTextBoxColumn
                {
                    Name = "RangeMin",
                    HeaderText = "Min Amount",
                    ReadOnly = false
                };
                dgvQuests.Columns.Add(colRangeMin);

                var colRangeMax = new DataGridViewTextBoxColumn
                {
                    Name = "RangeMax",
                    HeaderText = "Max Amount",
                    ReadOnly = false
                };
                dgvQuests.Columns.Add(colRangeMax);

                // Reward Type column
                var colRewardType = new DataGridViewComboBoxColumn
                {
                    DataPropertyName = "RewardType",
                    HeaderText = "Reward Type",
                    DataSource = Enum.GetValues(typeof(RewardType)),
                    FlatStyle = FlatStyle.Flat
                };
                dgvQuests.Columns.Add(colRewardType);

                // Reward Value column - set up with initial empty data source
                var colRewardValue = new DataGridViewComboBoxColumn
                {
                    Name = "RewardValue", // Add the Name property
                    DataPropertyName = "RewardValue",
                    HeaderText = "Reward Value",
                    FlatStyle = FlatStyle.Flat,
                    DataSource = new List<string> { "" } // Initial empty source
                };
                dgvQuests.Columns.Add(colRewardValue);

                // Reward Quantity column
                var colRewardQuantity = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "RewardQuantity",
                    HeaderText = "Quantity"
                };
                dgvQuests.Columns.Add(colRewardQuantity);

                dgvQuests.CellFormatting += DgvQuests_CellFormatting;
                dgvQuests.CellValueChanged += DgvQuests_CellValueChanged;
                dgvQuests.CurrentCellDirtyStateChanged += DgvQuests_CurrentCellDirtyStateChanged;

                // Button panel
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

                mainLayout.Controls.Add(dgvQuests, 0, 0);
                mainLayout.Controls.Add(buttonPanel, 0, 1);

                this.Controls.Add(mainLayout);
            }

            private void DgvQuests_CurrentCellDirtyStateChanged(object sender, EventArgs e)
            {
                if (dgvQuests.IsCurrentCellDirty)
                {
                    dgvQuests.CommitEdit(DataGridViewDataErrorContexts.Commit);
                }
            }

            private void LoadQuestsFromJson()
            {
                quests.Clear();
                if (string.IsNullOrEmpty(modulePath))
                    return;

                string questPath = Path.Combine(modulePath, "quests.json");
                if (File.Exists(questPath))
                {
                    try
                    {
                        string json = File.ReadAllText(questPath);
                        using (JsonDocument doc = JsonDocument.Parse(json))
                        {
                            var root = doc.RootElement;
                            if (root.TryGetProperty("quests", out var questsElement))
                            {
                                quests = JsonSerializer.Deserialize<List<Quest>>(questsElement.GetRawText()) ?? new List<Quest>();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error loading quests.json: " + ex.Message);
                    }
                }

                // Ensure all quests have proper IDs and arrays
                foreach (var quest in quests)
                {
                    if (string.IsNullOrEmpty(quest.Id))
                        quest.Id = Guid.NewGuid().ToString();
                    if (quest.TargetAmountRange == null || quest.TargetAmountRange.Length < 2)
                        quest.TargetAmountRange = new int[] { 1, 1 };
                }

                bindingSource.DataSource = quests;
                bindingSource.ResetBindings(false);
                
                // Update reward value combo after loading
                UpdateRewardValueCombo();
            }

            private void LoadItemsFromJson()
            {
                items.Clear();
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
                                items = JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText()) ?? new List<Item>();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error loading item.json: " + ex.Message);
                    }
                }

                // Cache item names
                itemNames = items.Select(i => i.Name).ToList();
                itemNames.Insert(0, "");
            }

            private void UpdateRewardValueCombo()
            {
                if (isUpdatingCombos) return;
                isUpdatingCombos = true;

                try
                {
                    var rewardValueColumn = dgvQuests.Columns["RewardValue"] as DataGridViewComboBoxColumn;
                    if (rewardValueColumn != null)
                    {
                        // For now, we'll keep it simple and show item names for all reward types
                        // This could be enhanced later to show different options based on reward type:
                        // - Item: item names
                        // - Trophy: trophy names/IDs
                        // - Experience: experience amounts
                        // - Vital_Values: vital value amounts
                        rewardValueColumn.DataSource = itemNames.ToList();
                    }
                }
                finally
                {
                    isUpdatingCombos = false;
                }
            }

            private void DgvQuests_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
            {
                if (e.RowIndex < 0 || e.RowIndex >= quests.Count || isUpdatingCombos) return;

                var quest = quests[e.RowIndex];
                var column = dgvQuests.Columns[e.ColumnIndex];

                if (column.Name == "RangeMin")
                {
                    e.Value = quest.TargetAmountRange?.Length > 0 ? quest.TargetAmountRange[0] : 1;
                }
                else if (column.Name == "RangeMax")
                {
                    e.Value = quest.TargetAmountRange?.Length > 1 ? quest.TargetAmountRange[1] : 1;
                }
                // Remove the RewardValue cell formatting that was causing the loop
            }

            private void DgvQuests_CellValueChanged(object sender, DataGridViewCellEventArgs e)
            {
                if (e.RowIndex < 0 || e.RowIndex >= quests.Count) return;

                var quest = quests[e.RowIndex];
                var column = dgvQuests.Columns[e.ColumnIndex];

                if (column.Name == "RangeMin" || column.Name == "RangeMax")
                {
                    if (quest.TargetAmountRange == null)
                        quest.TargetAmountRange = new int[2] { 1, 1 };

                    var cell = dgvQuests.Rows[e.RowIndex].Cells[e.ColumnIndex];
                    if (int.TryParse(cell.Value?.ToString(), out int value) && value > 0)
                    {
                        if (column.Name == "RangeMin")
                            quest.TargetAmountRange[0] = value;
                        else
                            quest.TargetAmountRange[1] = value;
                    }
                    UpdateQuestName(quest);
                }
                else if (column.DataPropertyName == "QuestType")
                {
                    UpdateQuestName(quest);
                }
                else if (column.DataPropertyName == "RewardType")
                {
                    // When reward type changes, update the combo box data source
                    UpdateRewardValueCombo();
                }

                bindingSource.ResetBindings(false);
            }

            private void UpdateQuestNames()
            {
                foreach (var quest in quests)
                {
                    UpdateQuestName(quest);
                }
            }

            private void UpdateQuestName(Quest quest)
            {
                if (quest.TargetAmountRange?.Length >= 2)
                {
                    int min = quest.TargetAmountRange[0];
                    int max = quest.TargetAmountRange[1];
                    
                    string amountText = min == max ? min.ToString() : $"{min}-{max}";
                    
                    // Generate quest name based on type
                    switch (quest.QuestType)
                    {
                        case QuestType.Boss:
                            quest.Name = min == max && min == 1 
                                ? $"Defeat {amountText} Boss" 
                                : $"Defeat {amountText} Bosses";
                            break;
                        case QuestType.Training:
                            quest.Name = min == max && min == 1 
                                ? $"Train {amountText} Time" 
                                : $"Train {amountText} Times";
                            break;
                        case QuestType.Battle:
                            quest.Name = min == max && min == 1 
                                ? $"Win {amountText} Battle" 
                                : $"Win {amountText} Battles";
                            break;
                        case QuestType.Feeding:
                            quest.Name = min == max && min == 1 
                                ? $"Eat {amountText} Time" 
                                : $"Eat {amountText} Times";
                            break;
                        case QuestType.Evolution:
                            quest.Name = min == max && min == 1 
                                ? $"Evolve {amountText} Time" 
                                : $"Evolve {amountText} Times";
                            break;
                        case QuestType.Armor_Evolution:
                            quest.Name = min == max && min == 1 
                                ? $"Armor Evolve {amountText} Time" 
                                : $"Armor Evolve {amountText} Times";
                            break;
                        case QuestType.Jogress:
                            quest.Name = min == max && min == 1 
                                ? $"Jogress {amountText} Time" 
                                : $"Jogress {amountText} Times";
                            break;
                        default:
                            quest.Name = $"Complete {amountText} {quest.QuestType}";
                            break;
                    }
                }
            }

            private void BtnAdd_Click(object sender, EventArgs e)
            {
                var newQuest = new Quest
                {
                    Id = Guid.NewGuid().ToString(),
                    Name = "New Quest",
                    QuestType = QuestType.Boss,
                    TargetAmountRange = new int[] { 1, 1 },
                    RewardType = RewardType.Item,
                    RewardValue = "",
                    RewardQuantity = 1
                };
                UpdateQuestName(newQuest);
                
                quests.Add(newQuest);
                bindingSource.ResetBindings(false);

                // Select the newly added row
                if (dgvQuests.Rows.Count > 0)
                {
                    try
                    {
                        dgvQuests.CurrentCell = dgvQuests.Rows[dgvQuests.Rows.Count - 1].Cells[0];
                    }
                    catch
                    {
                        // Ignore selection errors
                    }
                }
            }

            private void BtnRemove_Click(object sender, EventArgs e)
            {
                if (bindingSource.Current is Quest selectedQuest)
                {
                    var result = MessageBox.Show(
                        $"Do you want to remove the quest \"{selectedQuest.Name}\"?",
                        "Confirmation",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Warning
                    );
                    if (result == DialogResult.Yes)
                    {
                        quests.Remove(selectedQuest);
                        bindingSource.ResetBindings(false);
                    }
                }
            }
        }

        /// <summary>
        /// Panel for managing events.
        /// </summary>
        private class EventPanel : UserControl
        {
            private DataGridView dgvEvents;
            private BindingSource bindingSource;
            private Button btnAdd;
            private Button btnRemove;
            private List<Event> events = new List<Event>();
            private string modulePath;
            private Module module;
            private List<Item> items = new List<Item>();
            private List<string> itemNames = new List<string>(); // Cache item names
            private bool isUpdatingCombos = false; // Prevent recursive updates

            public EventPanel()
            {
                InitializeComponent();
            }

            public void SetModule(string modulePath, Module module)
            {
                this.modulePath = modulePath;
                this.module = module;
                LoadItemsFromJson();
                LoadEventsFromJson();
            }

            public void Save()
            {
                if (string.IsNullOrEmpty(modulePath) || events == null)
                    return;

                string eventPath = Path.Combine(modulePath, "events.json");
                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
                };
                var obj = new { events = events };
                try
                {
                    string json = JsonSerializer.Serialize(obj, options);
                    File.WriteAllText(eventPath, json);
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error saving events.json: " + ex.Message);
                }
            }

            private void InitializeComponent()
            {
                this.Dock = DockStyle.Fill;

                var mainLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 2,
                    ColumnCount = 1,
                    Padding = new Padding(8),
                    BackColor = SystemColors.Control
                };
                mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
                mainLayout.RowStyles.Add(new RowStyle(SizeType.Absolute, 40F));

                // Initialize BindingSource
                bindingSource = new BindingSource();

                dgvEvents = new DataGridView
                {
                    Dock = DockStyle.Fill,
                    AutoGenerateColumns = false,
                    AllowUserToAddRows = false,
                    AllowUserToDeleteRows = false,
                    RowHeadersVisible = false,
                    SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                    MultiSelect = false,
                    ReadOnly = false,
                    AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                    DataSource = bindingSource
                };

                // Name column
                var colName = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Name",
                    HeaderText = "Name",
                    ReadOnly = false
                };
                dgvEvents.Columns.Add(colName);

                // Global column
                var colGlobal = new DataGridViewCheckBoxColumn
                {
                    DataPropertyName = "Global",
                    HeaderText = "Global",
                    ReadOnly = false
                };
                dgvEvents.Columns.Add(colGlobal);

                // Event Type column
                var colEventType = new DataGridViewComboBoxColumn
                {
                    DataPropertyName = "Type",
                    HeaderText = "Type",
                    DataSource = Enum.GetValues(typeof(EventType)),
                    FlatStyle = FlatStyle.Flat
                };
                dgvEvents.Columns.Add(colEventType);

                // Chance Percent column
                var colChancePercent = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "ChancePercent",
                    HeaderText = "Chance %",
                    ReadOnly = false
                };
                dgvEvents.Columns.Add(colChancePercent);

                // Area column
                var colArea = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Area",
                    HeaderText = "Area",
                    ReadOnly = false
                };
                dgvEvents.Columns.Add(colArea);

                // Round column
                var colRound = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Round",
                    HeaderText = "Round",
                    ReadOnly = false
                };
                dgvEvents.Columns.Add(colRound);

                // Item column - set up with initial data source
                var colItem = new DataGridViewComboBoxColumn
                {
                    DataPropertyName = "Item",
                    HeaderText = "Item",
                    FlatStyle = FlatStyle.Flat,
                    DataSource = new List<string> { "" } // Initial empty source
                };
                colItem.Name = "Item"; // Add the Name property
                dgvEvents.Columns.Add(colItem);

                // Item Quantity column
                var colItemQuantity = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "ItemQuantity",
                    HeaderText = "Quantity"
                };
                dgvEvents.Columns.Add(colItemQuantity);

                // Remove the problematic CellFormatting event
                // dgvEvents.CellFormatting += DgvEvents_CellFormatting;

                // Button panel
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

                mainLayout.Controls.Add(dgvEvents, 0, 0);
                mainLayout.Controls.Add(buttonPanel, 0, 1);

                this.Controls.Add(mainLayout);
            }

            private void LoadEventsFromJson()
            {
                events.Clear();
                if (string.IsNullOrEmpty(modulePath))
                    return;

                string eventPath = Path.Combine(modulePath, "events.json");
                if (File.Exists(eventPath))
                {
                    try
                    {
                        string json = File.ReadAllText(eventPath);
                        using (JsonDocument doc = JsonDocument.Parse(json))
                        {
                            var root = doc.RootElement;
                            if (root.TryGetProperty("events", out var eventsElement))
                            {
                                events = JsonSerializer.Deserialize<List<Event>>(eventsElement.GetRawText()) ?? new List<Event>();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error loading events.json: " + ex.Message);
                    }
                }

                // Ensure all events have proper IDs
                foreach (var eventItem in events)
                {
                    if (string.IsNullOrEmpty(eventItem.Id))
                        eventItem.Id = Guid.NewGuid().ToString();
                }

                bindingSource.DataSource = events;
                bindingSource.ResetBindings(false);
                
                // Update item combo after loading
                UpdateItemCombo();
            }

            private void LoadItemsFromJson()
            {
                items.Clear();
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
                                items = JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText()) ?? new List<Item>();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error loading item.json: " + ex.Message);
                    }
                }

                // Cache item names
                itemNames = items.Select(i => i.Name).ToList();
                itemNames.Insert(0, "");
            }

            private void UpdateItemCombo()
            {
                if (isUpdatingCombos) return;
                isUpdatingCombos = true;

                try
                {
                    var itemColumn = dgvEvents.Columns["Item"] as DataGridViewComboBoxColumn;
                    if (itemColumn != null)
                    {
                        // Set the global data source for all cells in this column
                        itemColumn.DataSource = itemNames.ToList();
                    }
                }
                finally
                {
                    isUpdatingCombos = false;
                }
            }

            private void BtnAdd_Click(object sender, EventArgs e)
            {
                var newEvent = new Event
                {
                    Id = Guid.NewGuid().ToString(),
                    Name = "New Event",
                    Global = false,
                    Type = EventType.ItemPackage,
                    ChancePercent = 10.0,
                    Area = 1,
                    Round = 1,
                    Item = "",
                    ItemQuantity = 1
                };
                
                events.Add(newEvent);
                bindingSource.ResetBindings(false);

                // Select the newly added row
                if (dgvEvents.Rows.Count > 0)
                {
                    try
                    {
                        dgvEvents.CurrentCell = dgvEvents.Rows[dgvEvents.Rows.Count - 1].Cells[0];
                    }
                    catch
                    {
                        // Ignore selection errors
                    }
                }
            }

            private void BtnRemove_Click(object sender, EventArgs e)
            {
                if (bindingSource.Current is Event selectedEvent)
                {
                    var result = MessageBox.Show(
                        $"Do you want to remove the event \"{selectedEvent.Name}\"?",
                        "Confirmation",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Warning
                    );
                    if (result == DialogResult.Yes)
                    {
                        events.Remove(selectedEvent);
                        bindingSource.ResetBindings(false);
                    }
                }
            }
        }

        #endregion
    }
}