using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace OmnimonModuleEditor.Tabs
{
    // Visible Stats Editor Form - NEW
    public class VisibleStatsEditorForm : Form
    {
        private CheckedListBox checkedListBox;
        private Button btnOK;
        private Button btnCancel;
        private Button btnSelectAll;
        private Button btnSelectNone;

        public List<string> SelectedStats { get; private set; }

        public VisibleStatsEditorForm(List<string> currentSelection)
        {
            InitializeComponent();
            PopulateStats(currentSelection);
        }

        private void InitializeComponent()
        {
            this.Text = "Edit Visible Stats";
            this.Size = new Size(450, 550);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            var mainLayout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 3,
                ColumnCount = 1,
                Padding = new Padding(15)
            };
            mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));

            // Title and instructions
            var titleLabel = new Label
            {
                Text = "Select which stats should be visible in the game UI:",
                Dock = DockStyle.Fill,
                AutoSize = true,
                Font = new Font(SystemFonts.DefaultFont, FontStyle.Bold),
                Padding = new Padding(0, 0, 0, 10)
            };
            mainLayout.Controls.Add(titleLabel, 0, 0);

            // CheckedListBox
            checkedListBox = new CheckedListBox
            {
                Dock = DockStyle.Fill,
                CheckOnClick = true,
                IntegralHeight = false,
                AutoSize = false
            };
            mainLayout.Controls.Add(checkedListBox, 0, 1);

            // Buttons panel
            var buttonPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 1,
                ColumnCount = 4,
                Height = 40,
                Padding = new Padding(0, 10, 0, 0)
            };
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));

            btnSelectAll = new Button
            {
                Text = "Select All",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };
            btnSelectAll.Click += (s, e) =>
            {
                for (int i = 0; i < checkedListBox.Items.Count; i++)
                    checkedListBox.SetItemChecked(i, true);
            };

            btnSelectNone = new Button
            {
                Text = "Select None",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };
            btnSelectNone.Click += (s, e) =>
            {
                for (int i = 0; i < checkedListBox.Items.Count; i++)
                    checkedListBox.SetItemChecked(i, false);
            };

            btnOK = new Button
            {
                Text = "OK",
                DialogResult = DialogResult.OK,
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };

            btnCancel = new Button
            {
                Text = "Cancel",
                DialogResult = DialogResult.Cancel,
                Dock = DockStyle.Fill
            };

            buttonPanel.Controls.Add(btnSelectAll, 0, 0);
            buttonPanel.Controls.Add(btnSelectNone, 1, 0);
            buttonPanel.Controls.Add(btnOK, 2, 0);
            buttonPanel.Controls.Add(btnCancel, 3, 0);

            mainLayout.Controls.Add(buttonPanel, 0, 2);

            this.Controls.Add(mainLayout);
            this.AcceptButton = btnOK;
            this.CancelButton = btnCancel;

            btnOK.Click += BtnOK_Click;
        }

        private void PopulateStats(List<string> currentSelection)
        {
            checkedListBox.Items.Clear();

            string[] availableStats = {
                "Age", "Weight", "Hunger", "Strength", "Trophies", "Vital Values",
                "Level", "Experience", "Mistakes/Condition Hearts", "Sleep Disturbances",
                "Overfeed", "Injuries", "Effort", "Power", "DP", "Battles", "Win Rate",
                "Total Win Rate", "Evolution Timer", "Sleeps", "Wakes", "Poop Time",
                "Feed Time", "Flags"
            };

            foreach (string stat in availableStats)
            {
                int index = checkedListBox.Items.Add(stat);
                
                // Check if this stat is in the current selection
                if (currentSelection != null && currentSelection.Contains(stat))
                {
                    checkedListBox.SetItemChecked(index, true);
                }
            }
        }

        private void BtnOK_Click(object sender, EventArgs e)
        {
            SelectedStats = new List<string>();
            
            foreach (var item in checkedListBox.CheckedItems)
            {
                SelectedStats.Add(item.ToString());
            }
        }
    }

    // Group Unlock Editor Form
    public class GroupUnlockEditorForm : Form
    {
        private CheckedListBox checkedListBox;
        private Button btnOK;
        private Button btnCancel;
        private Button btnSelectAll;
        private Button btnSelectNone;
        
        public List<string> SelectedUnlocks { get; private set; }

        public GroupUnlockEditorForm(List<string> currentSelection, List<OmnimonModuleEditor.Models.Unlock> allUnlocks)
        {
            InitializeComponent();
            PopulateUnlocks(allUnlocks, currentSelection);
        }

        private void InitializeComponent()
        {
            this.Text = "Edit Group Unlock List";
            this.Size = new Size(450, 550);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            var mainLayout = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 3,
                ColumnCount = 1,
                Padding = new Padding(15)
            };
            mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));

            // Title and instructions
            var titleLabel = new Label
            {
                Text = "Select which unlocks must be completed for this group unlock to trigger:",
                Dock = DockStyle.Fill,
                AutoSize = true,
                Font = new Font(SystemFonts.DefaultFont, FontStyle.Bold),
                Padding = new Padding(0, 0, 0, 10)
            };
            mainLayout.Controls.Add(titleLabel, 0, 0);

            // CheckedListBox
            checkedListBox = new CheckedListBox
            {
                Dock = DockStyle.Fill,
                CheckOnClick = true,
                IntegralHeight = false,
                AutoSize = false
            };
            mainLayout.Controls.Add(checkedListBox, 0, 1);

            // Buttons panel
            var buttonPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 1,
                ColumnCount = 4,
                Height = 40,
                Padding = new Padding(0, 10, 0, 0)
            };
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
            buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));

            btnSelectAll = new Button
            {
                Text = "Select All",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };
            btnSelectAll.Click += (s, e) =>
            {
                for (int i = 0; i < checkedListBox.Items.Count; i++)
                    checkedListBox.SetItemChecked(i, true);
            };

            btnSelectNone = new Button
            {
                Text = "Select None",
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };
            btnSelectNone.Click += (s, e) =>
            {
                for (int i = 0; i < checkedListBox.Items.Count; i++)
                    checkedListBox.SetItemChecked(i, false);
            };

            btnOK = new Button
            {
                Text = "OK",
                DialogResult = DialogResult.OK,
                Dock = DockStyle.Fill,
                Margin = new Padding(0, 0, 5, 0)
            };

            btnCancel = new Button
            {
                Text = "Cancel",
                DialogResult = DialogResult.Cancel,
                Dock = DockStyle.Fill
            };

            buttonPanel.Controls.Add(btnSelectAll, 0, 0);
            buttonPanel.Controls.Add(btnSelectNone, 1, 0);
            buttonPanel.Controls.Add(btnOK, 2, 0);
            buttonPanel.Controls.Add(btnCancel, 3, 0);

            mainLayout.Controls.Add(buttonPanel, 0, 2);

            this.Controls.Add(mainLayout);
            this.AcceptButton = btnOK;
            this.CancelButton = btnCancel;

            btnOK.Click += BtnOK_Click;
        }

        private void PopulateUnlocks(List<OmnimonModuleEditor.Models.Unlock> allUnlocks, List<string> currentSelection)
        {
            checkedListBox.Items.Clear();
            
            if (allUnlocks != null)
            {
                foreach (var unlock in allUnlocks)
                {
                    if (unlock.Type != "group") // Don't allow group unlocks to reference other group unlocks to avoid circular dependencies
                    {
                        string displayText = $"{unlock.Label ?? unlock.Name ?? "Unnamed"} ({unlock.Type})";
                        var unlockItem = new UnlockItem { Unlock = unlock, DisplayText = displayText };
                        int index = checkedListBox.Items.Add(unlockItem);
                        
                        // Check if this unlock is in the current selection
                        if (currentSelection != null && currentSelection.Contains(unlock.Name))
                        {
                            checkedListBox.SetItemChecked(index, true);
                        }
                    }
                }
            }
        }

        private void BtnOK_Click(object sender, EventArgs e)
        {
            SelectedUnlocks = new List<string>();
            
            foreach (var item in checkedListBox.CheckedItems)
            {
                if (item is UnlockItem unlockItem)
                {
                    SelectedUnlocks.Add(unlockItem.Unlock.Name);
                }
            }
        }

        private class UnlockItem
        {
            public OmnimonModuleEditor.Models.Unlock Unlock { get; set; }
            public string DisplayText { get; set; }

            public override string ToString()
            {
                return DisplayText;
            }
        }
    }

    /// <summary>
    /// Tab for managing and editing the main module settings, unlocks, and backgrounds.
    /// </summary>
    public partial class ModuleTab : UserControl
    {
        private TabPage tabMain;
        private MainPanel mainPanel;
        private TabPage tabUnlocks;
        private UnlocksPanel unlocksPanel;
        private TabPage tabBackgrounds;
        private BackgroundsPanel backgroundsPanel;
        private TabControl tabControl;

        /// <summary>
        /// Initializes a new instance of the <see cref="ModuleTab"/> class.
        /// </summary>
        public ModuleTab()
        {
            InitializeComponent();
        }

        #region Initialization

        /// <summary>
        /// Initializes the layout and child controls.
        /// </summary>
        private void InitializeComponent()
        {
            this.tabControl = new TabControl();
            this.tabMain = new TabPage();
            this.mainPanel = new MainPanel();
            this.tabUnlocks = new TabPage();
            this.unlocksPanel = new UnlocksPanel();
            this.tabBackgrounds = new TabPage();
            this.backgroundsPanel = new BackgroundsPanel();

            this.tabControl.SuspendLayout();
            this.tabMain.SuspendLayout();
            this.tabUnlocks.SuspendLayout();
            this.tabBackgrounds.SuspendLayout();
            this.SuspendLayout();

            // TabControl
            this.tabControl.Controls.Add(this.tabMain);
            this.tabControl.Controls.Add(this.tabUnlocks);
            this.tabControl.Controls.Add(this.tabBackgrounds);
            this.tabControl.Dock = DockStyle.Fill;
            this.tabControl.Name = "tabControl";
            this.tabControl.SelectedIndex = 0;
            this.tabControl.Size = new Size(1634, 718);
            this.tabControl.TabIndex = 0;

            // Main Tab
            this.tabMain.Controls.Add(this.mainPanel);
            this.tabMain.Name = "tabMain";
            this.tabMain.Size = new Size(1626, 692);
            this.tabMain.TabIndex = 0;
            this.tabMain.Text = Properties.Resources.ModuleTab_TabMain ?? "Main";

            this.mainPanel.BackColor = SystemColors.Control;
            this.mainPanel.Dock = DockStyle.Fill;
            this.mainPanel.ModulePath = null;
            this.mainPanel.Name = "mainPanel";
            this.mainPanel.Size = new Size(1626, 692);
            this.mainPanel.TabIndex = 0;

            // Unlocks Tab
            this.tabUnlocks.Controls.Add(this.unlocksPanel);
            this.tabUnlocks.Name = "tabUnlocks";
            this.tabUnlocks.Size = new Size(192, 74);
            this.tabUnlocks.TabIndex = 1;
            this.tabUnlocks.Text = Properties.Resources.ModuleTab_TabUnlocks ?? "Unlocks";

            this.unlocksPanel.BackColor = SystemColors.Control;
            this.unlocksPanel.Dock = DockStyle.Fill;
            this.unlocksPanel.Name = "unlocksPanel";
            this.unlocksPanel.Size = new Size(192, 74);
            this.unlocksPanel.TabIndex = 0;

            // Backgrounds Tab
            this.tabBackgrounds.Controls.Add(this.backgroundsPanel);
            this.tabBackgrounds.Name = "tabBackgrounds";
            this.tabBackgrounds.Size = new Size(192, 74);
            this.tabBackgrounds.TabIndex = 2;
            this.tabBackgrounds.Text = Properties.Resources.ModuleTab_TabBackgrounds ?? "Backgrounds";

            this.backgroundsPanel.BackColor = SystemColors.Control;
            this.backgroundsPanel.Dock = DockStyle.Fill;
            this.backgroundsPanel.Name = "backgroundsPanel";
            this.backgroundsPanel.Size = new Size(192, 74);
            this.backgroundsPanel.TabIndex = 0;

            // ModuleTab
            this.Controls.Add(this.tabControl);
            this.Name = "ModuleTab";
            this.Size = new Size(1634, 718);

            this.tabControl.ResumeLayout(false);
            this.tabMain.ResumeLayout(false);
            this.tabUnlocks.ResumeLayout(false);
            this.tabBackgrounds.ResumeLayout(false);
            this.ResumeLayout(false);
        }

        #endregion

        #region Public API

        /// <summary>
        /// Sets the module path and reloads sprites in the main panel.
        /// </summary>
        public void SetModulePath(string modulePath)
        {
            foreach (TabPage tab in tabControl.TabPages)
            {
                if (tab.Controls.Count > 0 && tab.Controls[0] is MainPanel mainPanel)
                {
                    mainPanel.ModulePath = modulePath;
                    mainPanel.ReloadSprites();
                }
            }
        }

        /// <summary>
        /// Saves the current module data to module.json in the current module path.
        /// </summary>
        public void Save()
        {
            if (mainPanel == null || string.IsNullOrEmpty(mainPanel.ModulePath))
                return;

            var module = new OmnimonModuleEditor.Models.Module
            {
                Name = mainPanel.txtName?.Text ?? "",
                Version = mainPanel.txtVersion?.Text ?? "",
                Description = mainPanel.txtDescription?.Text ?? "",
                Author = mainPanel.txtAuthor?.Text ?? "",
                NameFormat = OmnimonModuleEditor.Utils.PetUtils.FixedNameFormat, // Always use fixed format
                Ruleset = mainPanel.cmbRuleset?.SelectedItem?.ToString() ?? "",
                AdventureMode = mainPanel.chkAdventureMode?.Checked ?? false,
                HighDefinitionSprites = mainPanel.chkHighDefinitionSprites?.Checked ?? false,
                VisibleStats = mainPanel.currentVisibleStats ?? "", // Use stored value
                CareMeatWeightGain = (int)(mainPanel.numCareMeatWeightGain?.Value ?? 0),
                CareMeatHungerGain = (float)(mainPanel.numCareMeatHungerGain?.Value ?? 0),
                CareMeatCareMistakeTime = (int)(mainPanel.numCareMeatCareMistakeTime?.Value ?? 0),
                CareOverfeedTimer = (int)(mainPanel.numCareOverfeedTimer?.Value ?? 0),
                CareConditionHeart = mainPanel.chkCareConditionHeart?.Checked ?? false,
                CareCanEatSleeping = mainPanel.chkCareCanEatSleeping?.Checked ?? false,
                CareBackToSleepTime = (int)(mainPanel.numCareBackToSleepTime?.Value ?? 0),
                CareEnableShakenEgg = mainPanel.chkCareEnableShakenEgg?.Checked ?? false,
                CareFlushDisturbanceSleep = mainPanel.chkCareFlushDisturbanceSleep?.Checked ?? true,
                CareProteinWeightGain = (int)(mainPanel.numCareProteinWeightGain?.Value ?? 0),
                CareProteinStrenghGain = (float)(mainPanel.numCareProteinStrenghGain?.Value ?? 0),
                CareProteinDpGain = (int)(mainPanel.numCareProteinDpGain?.Value ?? 0),
                CareProteinCareMistakeTime = (int)(mainPanel.numCareProteinCareMistakeTime?.Value ?? 0),
                CareProteinOverdoseMax = (int)(mainPanel.numCareProteinOverdoseMax?.Value ?? 0),
                CareProteinPenalty = (int)(mainPanel.numCareProteinPenalty?.Value ?? 10),
                CareDisturbancePenaltyMax = (int)(mainPanel.numCareDisturbancePenaltyMax?.Value ?? 0),
                CareSleepCareMistakeTimer = (int)(mainPanel.numCareSleepCareMistakeTimer?.Value ?? 0),
                TrainingEffortGain = (int)(mainPanel.numTrainingEffortGain?.Value ?? 0),
                TrainingStrenghGainWin = (int)(mainPanel.numTrainingStrenghGainWin?.Value ?? 0),
                TrainingStrenghGainLose = (int)(mainPanel.numTrainingStrenghGainLose?.Value ?? 0),
                TrainingStrenghMultiplier = (float)(mainPanel.numTrainingStrenghMultiplier?.Value ?? 0),
                TrainingWeightWin = (int)(mainPanel.numTrainingWeightWin?.Value ?? 0),
                TrainingWeightLose = (int)(mainPanel.numTrainingWeightLose?.Value ?? 0),
                TraitedEggStartingLevel = (int)(mainPanel.numTraitedEggStartingLevel?.Value ?? 0),
                ReverseAtkFrames = mainPanel.chkReverseAtkFrames?.Checked ?? false,
                BattleBaseSickChanceWin = (int)(mainPanel.numBattleBaseSickChanceWin?.Value ?? 0),
                BattleBaseSickChanceLose = (int)(mainPanel.numBattleBaseSickChanceLose?.Value ?? 0),
                BattleAtributeAdvantage = (int)(mainPanel.numBattleAtributeAdvantage?.Value ?? 0),
                BattleGlobalHitPoints = (int)(mainPanel.numBattleGlobalHitPoints?.Value ?? 0),
                BattleSequentialRounds = mainPanel.chkBattleSequentialRounds?.Checked ?? false,
                DeathMaxInjuries = (int)(mainPanel.numDeathMaxInjuries?.Value ?? 0),
                DeathCareMistake = (int)(mainPanel.numDeathCareMistake?.Value ?? 0),
                DeathSickTimer = (int)(mainPanel.numDeathSickTimer?.Value ?? 0),
                DeathHungerTimer = (int)(mainPanel.numDeathHungerTimer?.Value ?? 0),
                DeathStarvationCount = (int)(mainPanel.numDeathStarvationCount?.Value ?? 0),
                DeathStrengthTimer = (int)(mainPanel.numDeathStrengthTimer?.Value ?? 0),
                DeathStage45Mistake = (int)(mainPanel.numDeathStage45Mistake?.Value ?? 0),
                DeathStage67Mistake = (int)(mainPanel.numDeathStage67Mistake?.Value ?? 0),
                DeathSaveByBPress = (int)(mainPanel.numDeathSaveByBPress?.Value ?? 0),
                DeathSaveByShake = (int)(mainPanel.numDeathSaveByShake?.Value ?? 0),
                DeathOldAge = (int)(mainPanel.numDeathOldAge?.Value ?? 0),
                VitalValueBase = (int)(mainPanel.numVitalValueBase?.Value ?? 0),
                VitalValueLoss = (int)(mainPanel.numVitalValueLoss?.Value ?? 0)
            };

            if (backgroundsPanel != null)
                module.Backgrounds = backgroundsPanel.GetBackgrounds();

            // Salvar os Unlocks do painel
            if (unlocksPanel != null)
                module.Unlocks = unlocksPanel.GetUnlocks();

            if (module.Unlocks == null)
                module.Unlocks = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock>();
            if (module.Backgrounds == null)
                module.Backgrounds = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>();

            string filePath = Path.Combine(mainPanel.ModulePath, "module.json");
            var options = new JsonSerializerOptions { WriteIndented = true };
            File.WriteAllText(filePath, JsonSerializer.Serialize(module, options));
        }

        /// <summary>
        /// Loads the module data into the UI.
        /// </summary>
        public void LoadFromModule(OmnimonModuleEditor.Models.Module module)
        {
            if (mainPanel == null || module == null)
                return;

            // General
            mainPanel.txtName.Text = module.Name ?? "";
            mainPanel.txtVersion.Text = module.Version ?? "";
            mainPanel.txtDescription.Text = module.Description ?? "";
            mainPanel.txtAuthor.Text = module.Author ?? "";
            mainPanel.txtNameFormat.Text = OmnimonModuleEditor.Utils.PetUtils.FixedNameFormat; // Always show fixed format
            if (mainPanel.cmbRuleset.Items.Contains(module.Ruleset))
                mainPanel.cmbRuleset.SelectedItem = module.Ruleset;
            else if (mainPanel.cmbRuleset.Items.Count > 0)
                mainPanel.cmbRuleset.SelectedIndex = 0;
            mainPanel.chkAdventureMode.Checked = module.AdventureMode;

            // High Definition Sprites
            mainPanel.chkHighDefinitionSprites.Checked = module.HighDefinitionSprites;

            // Visible Stats - store in currentVisibleStats field
            if (!string.IsNullOrWhiteSpace(module.VisibleStats))
            {
                mainPanel.currentVisibleStats = module.VisibleStats;
            }
            else
            {
                // Default: all stats are visible for old modules
                string[] availableStats = {
                    "Age", "Weight", "Hunger", "Strength", "Trophies", "Vital Values",
                    "Level", "Experience", "Mistakes/Condition Hearts", "Sleep Disturbances",
                    "Overfeed", "Injuries", "Effort", "Power", "DP", "Battles", "Win Rate",
                    "Total Win Rate", "Evolution Timer", "Sleeps", "Wakes", "Poop Time",
                    "Feed Time", "Flags"
                };
                mainPanel.currentVisibleStats = string.Join(",", availableStats);
            }

            // Care Meat
            mainPanel.numCareMeatWeightGain.Value = module.CareMeatWeightGain;
            mainPanel.numCareMeatHungerGain.Value = (decimal)module.CareMeatHungerGain;
            mainPanel.numCareMeatCareMistakeTime.Value = module.CareMeatCareMistakeTime;
            mainPanel.numCareOverfeedTimer.Value = module.CareOverfeedTimer;
            mainPanel.chkCareConditionHeart.Checked = module.CareConditionHeart;
            mainPanel.chkCareCanEatSleeping.Checked = module.CareCanEatSleeping;
            mainPanel.numCareBackToSleepTime.Value = module.CareBackToSleepTime;
            mainPanel.chkCareEnableShakenEgg.Checked = module.CareEnableShakenEgg;
            mainPanel.chkCareFlushDisturbanceSleep.Checked = module.CareFlushDisturbanceSleep;

            // Care Protein
            mainPanel.numCareProteinWeightGain.Value = module.CareProteinWeightGain;
            mainPanel.numCareProteinStrenghGain.Value = (decimal)module.CareProteinStrenghGain;
            mainPanel.numCareProteinDpGain.Value = module.CareProteinDpGain;
            mainPanel.numCareProteinCareMistakeTime.Value = module.CareProteinCareMistakeTime;
            mainPanel.numCareProteinOverdoseMax.Value = module.CareProteinOverdoseMax;
            mainPanel.numCareProteinPenalty.Value = module.CareProteinPenalty ?? 10;
            mainPanel.numCareDisturbancePenaltyMax.Value = module.CareDisturbancePenaltyMax;

            // Care Sleep
            mainPanel.numCareSleepCareMistakeTimer.Value = module.CareSleepCareMistakeTimer;

            // Training
            mainPanel.numTrainingStrenghGainWin.Value = module.TrainingStrenghGainWin;
            mainPanel.numTrainingStrenghGainLose.Value = module.TrainingStrenghGainLose;
            mainPanel.numTrainingStrenghMultiplier.Value = (decimal)module.TrainingStrenghMultiplier;
            mainPanel.numTrainingWeightWin.Value = module.TrainingWeightWin;
            mainPanel.numTrainingWeightLose.Value = module.TrainingWeightLose;
            mainPanel.numTraitedEggStartingLevel.Value = module.TraitedEggStartingLevel;
            mainPanel.chkReverseAtkFrames.Checked = module.ReverseAtkFrames;

            // Battle
            mainPanel.numBattleBaseSickChanceWin.Value = module.BattleBaseSickChanceWin;
            mainPanel.numBattleBaseSickChanceLose.Value = module.BattleBaseSickChanceLose;
            mainPanel.numBattleAtributeAdvantage.Value = module.BattleAtributeAdvantage;
            mainPanel.numBattleGlobalHitPoints.Value = module.BattleGlobalHitPoints;
            mainPanel.chkBattleSequentialRounds.Checked = module.BattleSequentialRounds;

            // Death
            mainPanel.numDeathMaxInjuries.Value = module.DeathMaxInjuries;
            mainPanel.numDeathCareMistake.Value = module.DeathCareMistake;
            mainPanel.numDeathSickTimer.Value = module.DeathSickTimer;
            mainPanel.numDeathHungerTimer.Value = module.DeathHungerTimer;
            mainPanel.numDeathStarvationCount.Value = module.DeathStarvationCount;
            mainPanel.numDeathStrengthTimer.Value = module.DeathStrengthTimer;
            mainPanel.numDeathStage45Mistake.Value = module.DeathStage45Mistake;
            mainPanel.numDeathStage67Mistake.Value = module.DeathStage67Mistake;
            mainPanel.numDeathSaveByBPress.Value = module.DeathSaveByBPress;
            mainPanel.numDeathSaveByShake.Value = module.DeathSaveByShake;
            mainPanel.numDeathOldAge.Value = module.DeathOldAge;

            // Vital Values - NEW
            mainPanel.numVitalValueBase.Value = module.VitalValueBase;
            mainPanel.numVitalValueLoss.Value = module.VitalValueLoss;

            // Backgrounds
            if (backgroundsPanel != null)
                backgroundsPanel.LoadBackgrounds(module.Backgrounds ?? new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>(), mainPanel.ModulePath);

            // Unlocks
            if (unlocksPanel != null)
            {
                var pets = OmnimonModuleEditor.Utils.PetUtils.LoadPetsFromJson(mainPanel.ModulePath);
                unlocksPanel.LoadUnlocks(module.Unlocks ?? new System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock>(), pets);
            }
        }

        #endregion

        #region Internal Classes

        // Main tab panel (sprites and refresh)
        private class MainPanel : Panel
        {
            public string ModulePath { get; set; }

            private SpriteBox pbFlag;
            private SpriteBox pbLogo;
            private SpriteBox pbBattleIcon;
            private Button btnRefresh;

            // Controls for Module fields
            public TextBox txtName, txtVersion, txtDescription, txtAuthor, txtNameFormat;
            public ComboBox cmbRuleset;
            public CheckBox chkAdventureMode;

            // Care Meat
            public NumericUpDown numCareMeatWeightGain, numCareMeatHungerGain, numCareMeatCareMistakeTime, numCareOverfeedTimer;
            public CheckBox chkCareConditionHeart, chkCareCanEatSleeping, chkCareEnableShakenEgg, chkCareFlushDisturbanceSleep;
            public NumericUpDown numCareBackToSleepTime;

            // Care Protein
            public NumericUpDown numCareProteinWeightGain, numCareProteinStrenghGain, numCareProteinDpGain, numCareProteinCareMistakeTime, numCareProteinOverdoseMax, numCareProteinPenalty, numCareDisturbancePenaltyMax;

            // Care Sleep
            public NumericUpDown numCareSleepCareMistakeTimer;

            // Training
            public NumericUpDown numTrainingEffortGain, numTrainingStrenghGainWin, numTrainingStrenghGainLose, numTrainingStrenghMultiplier, numTrainingWeightWin, numTrainingWeightLose, numTraitedEggStartingLevel;
            public CheckBox chkReverseAtkFrames;

            // Battle
            public NumericUpDown numBattleBaseSickChanceWin, numBattleBaseSickChanceLose, numBattleAtributeAdvantage, numBattleGlobalHitPoints;
            public CheckBox chkBattleSequentialRounds;

            // Death
            public NumericUpDown numDeathMaxInjuries, numDeathCareMistake, numDeathSickTimer, numDeathHungerTimer, numDeathStarvationCount, numDeathStrengthTimer, numDeathStage45Mistake, numDeathStage67Mistake, numDeathSaveByBPress, numDeathSaveByShake, numDeathOldAge;

            // Vital Values - NEW
            public NumericUpDown numVitalValueBase, numVitalValueLoss;

            // High Definition Sprites
            public CheckBox chkHighDefinitionSprites;

            // Visible Stats - NEW (stored as string, button to edit)
            public string currentVisibleStats;
            private Button btnEditVisibleStats;

            public MainPanel()
            {
                InitializeLayout();
            }

            private void InitializeLayout()
            {
                this.BackColor = SystemColors.Control;

                // --- TOP SECTION: SPRITES ON LEFT, MAIN FIELDS ON RIGHT ---
                var topSection = new TableLayoutPanel
                {
                    RowCount = 1,
                    ColumnCount = 2,
                    Dock = DockStyle.Top,
                    Height = 180,
                    AutoSize = false,
                    Padding = new Padding(8)
                };
                topSection.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 400)); // Sprites column
                topSection.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100)); // Main fields column

                // --- SPRITES SECTION (LEFT) ---
                var spriteTable = new TableLayoutPanel
                {
                    RowCount = 2,
                    ColumnCount = 3,
                    Dock = DockStyle.Fill,
                    CellBorderStyle = TableLayoutPanelCellBorderStyle.None,
                    AutoSize = false
                };
                spriteTable.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 60));   // Flag
                spriteTable.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 280));  // Logo
                spriteTable.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 60));   // BattleIcon
                spriteTable.RowStyles.Add(new RowStyle(SizeType.Absolute, 120)); // Sprites
                spriteTable.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));  // Labels

                pbFlag = new SpriteBox(48, 48, "not found");
                pbFlag.Click += (s, e) => SelectAndReplaceSprite("Flag.png");
                pbLogo = new SpriteBox(240, 120, "not found");
                pbLogo.Click += (s, e) => SelectAndReplaceSprite("logo.png");
                pbBattleIcon = new SpriteBox(48, 48, "not found");
                pbBattleIcon.Click += (s, e) => SelectAndReplaceSprite("BattleIcon.png");

                var lblFlag = new Label
                {
                    Text = "Flag",
                    TextAlign = ContentAlignment.MiddleCenter,
                    Dock = DockStyle.Fill,
                    Font = new Font(FontFamily.GenericSansSerif, 10, FontStyle.Bold)
                };
                var lblLogo = new Label
                {
                    Text = "Logo",
                    TextAlign = ContentAlignment.MiddleCenter,
                    Dock = DockStyle.Fill,
                    Font = new Font(FontFamily.GenericSansSerif, 10, FontStyle.Bold)
                };
                var lblBattleIcon = new Label
                {
                    Text = "BattleIcon",
                    TextAlign = ContentAlignment.MiddleCenter,
                    Dock = DockStyle.Fill,
                    Font = new Font(FontFamily.GenericSansSerif, 10, FontStyle.Bold),
                    AutoSize = false
                };

                spriteTable.Controls.Add(pbFlag, 0, 0);
                spriteTable.Controls.Add(pbLogo, 1, 0);
                spriteTable.Controls.Add(pbBattleIcon, 2, 0);
                spriteTable.Controls.Add(lblFlag, 0, 1);
                spriteTable.Controls.Add(lblLogo, 1, 1);
                spriteTable.Controls.Add(lblBattleIcon, 2, 1);

                // --- MAIN FIELDS SECTION (RIGHT) ---
                var mainFieldsTable = new TableLayoutPanel
                {
                    RowCount = 4, // Back to 4 rows - removing HD and Visible Stats
                    ColumnCount = 2,
                    Dock = DockStyle.Fill,
                    Padding = new Padding(20, 0, 0, 0)
                };
                mainFieldsTable.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 120));
                mainFieldsTable.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));

                // Create main fields
                txtName = new TextBox() { Width = 200 };
                txtVersion = new TextBox() { Width = 200 };
                txtDescription = new TextBox() { Width = 200, Multiline = true, Height = 60, ScrollBars = ScrollBars.Vertical };
                txtAuthor = new TextBox() { Width = 200 };

                // Add fields to table - ONLY the basic 4 fields
                var mainFields = new (string, Control)[]
                {
                    ("Name:", txtName),
                    ("Version:", txtVersion),
                    ("Description:", txtDescription),
                    ("Author:", txtAuthor)
                };

                for (int i = 0; i < mainFields.Length; i++)
                {
                    mainFieldsTable.Controls.Add(new Label() 
                    { 
                        Text = mainFields[i].Item1, 
                        Anchor = AnchorStyles.Right, 
                        TextAlign = ContentAlignment.MiddleRight, 
                        AutoSize = true 
                    }, 0, i);
                    mainFieldsTable.Controls.Add(mainFields[i].Item2, 1, i);
                }

                // Add refresh button
                btnRefresh = new Button
                {
                    Text = "Refresh",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Top | AnchorStyles.Right
                };
                btnRefresh.Click += (s, e) => ReloadSprites();

                // Add sections to top layout
                topSection.Controls.Add(spriteTable, 0, 0);
                topSection.Controls.Add(mainFieldsTable, 1, 0);

                // --- CONFIGURATION FIELDS TABLE (3 columns, each with label+input) ---
                var fieldsTable = new TableLayoutPanel
                {
                    ColumnCount = 6, // 3 columns: label+input, label+input, label+input
                    Dock = DockStyle.Fill,
                    AutoSize = true,
                    Padding = new Padding(20, 0, 20, 0)
                };
                for (int i = 0; i < 6; i++)
                    fieldsTable.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 16.66f));

                // Configuration fields (moved main fields out of here)
                var col1 = new (string, Control)[]
                {
                    ("Name Format:", txtNameFormat = new TextBox() { Width = 140, Text = "$_dmc", Enabled = false }),
                    ("Ruleset:", cmbRuleset = new ComboBox() { DropDownStyle = ComboBoxStyle.DropDownList, Width = 140 }),
                    ("Adventure Mode:", chkAdventureMode = new CheckBox()),
                    ("Training Effort Gain:", numTrainingEffortGain = CreateNumeric(0, 100, 1)),
                    ("Training Strength Gain Win:", numTrainingStrenghGainWin = CreateNumeric(0, 100, 1)),
                    ("Training Strength Gain Lose:", numTrainingStrenghGainLose = CreateNumeric(0, 100, 1)),
                    ("Training Strength Multiplier:", numTrainingStrenghMultiplier = CreateFloatNumeric(0, 10, 1)),
                    ("Training Weight Win:", numTrainingWeightWin = CreateNumeric(0, 100, 4)),
                    ("Training Weight Lose:", numTrainingWeightLose = CreateNumeric(0, 100, 1)),
                    ("Traited Egg Starting Level:", numTraitedEggStartingLevel = CreateNumeric(0, 100, 3)),
                    ("Reverse Atk Frames:", chkReverseAtkFrames = new CheckBox()),
                    ("Battle Base Sick Chance Win:", numBattleBaseSickChanceWin = CreateNumeric(0, 100, 10)),
                    ("Battle Base Sick Chance Lose:", numBattleBaseSickChanceLose = CreateNumeric(0, 100, 10)),
                    ("Battle Atribute Advantage:", numBattleAtributeAdvantage = CreateNumeric(0, 100, 5)),
                    ("Battle Global Hit Points:", numBattleGlobalHitPoints = CreateNumeric(0, 100, 4)),
                    ("Battle Sequential Rounds:", chkBattleSequentialRounds = new CheckBox()),
                    ("", new Label()),
                };

                // Create the HD Sprites and Visible Stats controls properly
                chkHighDefinitionSprites = new CheckBox
                {
                    Text = "High Definition Sprites",
                    AutoSize = true
                };

                btnEditVisibleStats = new Button
                {
                    Text = "Edit Visible Stats...",
                    Width = 140,
                    Height = 25
                };
                btnEditVisibleStats.Click += (s, e) =>
                {
                    var currentStats = new List<string>();
                    if (!string.IsNullOrWhiteSpace(currentVisibleStats))
                    {
                        currentStats = currentVisibleStats.Split(',').Select(stat => stat.Trim()).ToList();
                    }

                    using (var form = new VisibleStatsEditorForm(currentStats))
                    {
                        if (form.ShowDialog() == DialogResult.OK)
                        {
                            currentVisibleStats = string.Join(",", form.SelectedStats);
                        }
                    }
                };

                // Now insert HD Sprites and Visible Stats after Adventure Mode
                var col1Updated = new List<(string, Control)>(col1);
                col1Updated.Insert(3, ("HD Sprites:", chkHighDefinitionSprites));
                col1Updated.Insert(4, ("Visible Stats:", btnEditVisibleStats));
                col1 = col1Updated.ToArray();

                cmbRuleset.Items.AddRange(new string[] { "dmc", "penc", "dmx", "vb" });
                cmbRuleset.SelectedIndex = 0;

                var col2 = new (string, Control)[]
                {
                    ("Care Meat Weight Gain:", numCareMeatWeightGain = CreateNumeric(0, 100, 1)),
                    ("Care Meat Hunger Gain:", numCareMeatHungerGain = CreateFloatNumeric(0, 100, 1)),
                    ("Care Meat Care Mistake Time:", numCareMeatCareMistakeTime = CreateNumeric(1, 1000, 10)),
                    ("Care Overfeed Timer:", numCareOverfeedTimer = CreateNumeric(1, 10000, 120)),
                    ("Care Condition Heart:", chkCareConditionHeart = new CheckBox()),
                    ("Care Can Eat Sleeping:", chkCareCanEatSleeping = new CheckBox() { Checked = true }),
                    ("Care Back To Sleep Time:", numCareBackToSleepTime = CreateNumeric(1, 1000, 10)),
                    ("Care Enable Shaken Egg:", chkCareEnableShakenEgg = new CheckBox()),
                    ("Care Flush Disturbance Sleep:", chkCareFlushDisturbanceSleep = new CheckBox() { Checked = true }),
                    ("Care Protein Weight Gain:", numCareProteinWeightGain = CreateNumeric(0, 100, 1)),
                    ("Care Protein Strengh Gain:", numCareProteinStrenghGain = CreateFloatNumeric(0, 100, 1)),
                    ("Care Protein Dp Gain:", numCareProteinDpGain = CreateNumeric(0, 100, 0)),
                    ("Care Protein Care Mistake Time:", numCareProteinCareMistakeTime = CreateNumeric(0, 1000, 10)),
                    ("Care Protein Overdose Max:", numCareProteinOverdoseMax = CreateNumeric(0, 100, 7)),
                    ("Care Protein Penalty:", numCareProteinPenalty = CreateNumeric(0, 100, 10)),
                    ("Care Disturbance Penalty Max:", numCareDisturbancePenaltyMax = CreateNumeric(0, 100, 0)),
                    ("Care Sleep Care Mistake Timer:", numCareSleepCareMistakeTimer = CreateNumeric(0, 1000, 60)),
                    ("", new Label()),
                };

                var col3 = new (string, Control)[]
                {
                    ("Death Max Injuries:", numDeathMaxInjuries = CreateNumeric(0, 100, 15)),
                    ("Death Care Mistake:", numDeathCareMistake = CreateNumeric(0, 100, 20)),
                    ("Death Sick Timer:", numDeathSickTimer = CreateNumeric(0, 10000, 360)),
                    ("Death Hunger Timer:", numDeathHungerTimer = CreateNumeric(0, 10000, 720)),
                    ("Death Starvation Count:", numDeathStarvationCount = CreateNumeric(0, 100, 0)),
                    ("Death Strength Timer:", numDeathStrengthTimer = CreateNumeric(0, 10000, 720)),
                    ("Death Stage45 Mistake:", numDeathStage45Mistake = CreateNumeric(0, 100, 5)),
                    ("Death Stage67 Mistake:", numDeathStage67Mistake = CreateNumeric(0, 100, 5)),
                    ("Death Save By B Press:", numDeathSaveByBPress = CreateNumeric(0, 100, 0)),
                    ("Death Save By Shake:", numDeathSaveByShake = CreateNumeric(0, 100, 0)),
                    ("Death Old Age:", numDeathOldAge = CreateNumeric(0, 999999, 0)),
                    ("Vital Value Base:", numVitalValueBase = CreateNumeric(0, 1000, 1)),
                    ("Vital Value Loss:", numVitalValueLoss = CreateNumeric(0, 1000, 1)),
                    ("", new Label()),
                };

                // Descobrir o maior número de linhas
                int maxRows = Math.Max(col1.Length, Math.Max(col2.Length, col3.Length));
                fieldsTable.RowCount = maxRows;

                for (int i = 0; i < maxRows; i++)
                {
                    if (i < col1.Length)
                    {
                        fieldsTable.Controls.Add(new Label() { Text = col1[i].Item1, Anchor = AnchorStyles.Right, TextAlign = ContentAlignment.MiddleRight, AutoSize = true }, 0, i);
                        fieldsTable.Controls.Add(col1[i].Item2, 1, i);
                    }
                    else
                    {
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 0, i);
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 1, i);
                    }

                    if (i < col2.Length)
                    {
                        fieldsTable.Controls.Add(new Label() { Text = col2[i].Item1, Anchor = AnchorStyles.Right, TextAlign = ContentAlignment.MiddleRight, AutoSize = true }, 2, i);
                        fieldsTable.Controls.Add(col2[i].Item2, 3, i);
                    }
                    else
                    {
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 2, i);
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 3, i);
                    }

                    if (i < col3.Length)
                    {
                        fieldsTable.Controls.Add(new Label() { Text = col3[i].Item1, Anchor = AnchorStyles.Right, TextAlign = ContentAlignment.MiddleRight, AutoSize = true }, 4, i);
                        fieldsTable.Controls.Add(col3[i].Item2, 5, i);
                    }
                    else
                    {
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 4, i);
                        fieldsTable.Controls.Add(new Label() { Text = "", AutoSize = true }, 5, i);
                    }
                }

                // --- ROOT LAYOUT ---
                var rootTable = new TableLayoutPanel
                {
                    RowCount = 2,
                    ColumnCount = 1,
                    Dock = DockStyle.Fill,
                    AutoSize = true
                };
                rootTable.RowStyles.Add(new RowStyle(SizeType.Absolute, 200)); // Top section
                rootTable.RowStyles.Add(new RowStyle(SizeType.Percent, 100));  // Configuration fields
                rootTable.Controls.Add(topSection, 0, 0);
                rootTable.Controls.Add(fieldsTable, 0, 1);

                this.Controls.Add(rootTable);
                this.Controls.Add(btnRefresh);

                this.Resize += (s, e) =>
                {
                    btnRefresh.Left = this.Width - btnRefresh.Width - 20;
                    btnRefresh.Top = 10;
                };
                btnRefresh.Left = this.Width - btnRefresh.Width - 20;
                btnRefresh.Top = 10;

                ReloadSprites();
            }

            private NumericUpDown CreateNumeric(int min, int max, int value)
            {
                var num = new NumericUpDown
                {
                    Minimum = min,
                    Maximum = max,
                    Value = value,
                    Width = 80
                };
                return num;
            }

            private NumericUpDown CreateFloatNumeric(decimal min, decimal max, decimal value, decimal increment = 0.5m)
            {
                var num = new NumericUpDown
                {
                    Minimum = min,
                    Maximum = max,
                    Value = value,
                    Width = 80,
                    DecimalPlaces = 2,
                    Increment = increment
                };
                return num;
            }

            public void ReloadSprites()
            {
                pbFlag.LoadSprite(string.IsNullOrEmpty(ModulePath) ? null : Path.Combine(ModulePath, "Flag.png"));
                pbLogo.LoadSprite(string.IsNullOrEmpty(ModulePath) ? null : Path.Combine(ModulePath, "logo.png"));
                pbBattleIcon.LoadSprite(string.IsNullOrEmpty(ModulePath) ? null : Path.Combine(ModulePath, "BattleIcon.png"));
            }

            private void SelectAndReplaceSprite(string fileName)
            {
                if (string.IsNullOrEmpty(ModulePath))
                    return;

                using (var dialog = new OpenFileDialog())
                {
                    dialog.Title = $"Select {fileName}";
                    dialog.Filter = "PNG files (*.png)|*.png";
                    dialog.InitialDirectory = ModulePath;
                    if (dialog.ShowDialog() == DialogResult.OK)
                    {
                        string destPath = Path.Combine(ModulePath, fileName);
                        try
                        {
                            File.Copy(dialog.FileName, destPath, true);
                            ReloadSprites();
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show("Failed to copy image: " + ex.Message);
                        }
                    }
                }
            }
        }

        // SpriteBox: PictureBox with border and not found logic
        private class SpriteBox : Control
        {
            private readonly int spriteWidth;
            private readonly int spriteHeight;
            private readonly string notFoundText;
            private Image spriteImage;

            public SpriteBox(int width, int height, string notFoundText)
            {
                this.spriteWidth = width;
                this.spriteHeight = height;
                this.notFoundText = notFoundText;
                this.Size = new Size(width, height);
                this.DoubleBuffered = true;
                this.Cursor = Cursors.Hand;
                this.TabStop = false;
            }

            public void LoadSprite(string filePath)
            {
                if (!string.IsNullOrEmpty(filePath) && File.Exists(filePath))
                {
                    try
                    {
                        using (var bmpTemp = new Bitmap(filePath))
                        {
                            spriteImage = new Bitmap(bmpTemp);
                        }
                    }
                    catch
                    {
                        spriteImage = null;
                    }
                }
                else
                {
                    spriteImage = null;
                }
                this.Invalidate();
            }

            protected override void OnPaint(PaintEventArgs e)
            {
                base.OnPaint(e);
                var g = e.Graphics;
                // White background
                using (var bg = new SolidBrush(Color.White))
                    g.FillRectangle(bg, 0, 0, spriteWidth, spriteHeight);

                // Draw image or not found
                if (spriteImage != null)
                {
                    // Center and fit image
                    var rect = new Rectangle(0, 0, spriteWidth, spriteHeight);
                    g.DrawImage(spriteImage, rect);
                }
                else
                {
                    // Draw not found text centered
                    using (var sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
                    using (var font = new Font(FontFamily.GenericSansSerif, 9, FontStyle.Bold))
                    using (var brush = new SolidBrush(Color.Red))
                    {
                        g.DrawString(notFoundText, font, brush, new RectangleF(0, 0, spriteWidth, spriteHeight), sf);
                    }
                }
                // Draw thin border
                using (var pen = new Pen(Color.Gray, 1))
                    g.DrawRectangle(pen, 0, 0, spriteWidth - 1, spriteHeight - 1);
            }
        }

        // Unlocks tab panel (functional)
        private class UnlocksPanel : Panel
        {
            private DataGridView dgvUnlocks;
            private BindingSource bindingSource;
            private Button btnAdd;
            private Button btnRemove;
            private System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock> unlocks;
            private List<OmnimonModuleEditor.Models.Pet> pets;

            public UnlocksPanel()
            {
                this.Dock = DockStyle.Fill;
                this.BackColor = SystemColors.Control;

                dgvUnlocks = new DataGridView
                {
                    Dock = DockStyle.Fill,
                    AutoGenerateColumns = false,
                    AllowUserToAddRows = false,
                    AllowUserToDeleteRows = false,
                    RowHeadersVisible = false,
                    SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                    MultiSelect = false,
                    ReadOnly = false,
                    AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
                };

                // Name column
                var colName = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Name",
                    HeaderText = "Name",
                    ReadOnly = false
                };
                dgvUnlocks.Columns.Add(colName);

                // Label column
                var colLabel = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Label",
                    HeaderText = "Label",
                    ReadOnly = false
                };
                dgvUnlocks.Columns.Add(colLabel);

                // Type column (ComboBox)
                var colType = new DataGridViewComboBoxColumn
                {
                    DataPropertyName = "Type",
                    HeaderText = "Type",
                    DataSource = new[] { "egg", "adventure", "evolution", "digidex", "group", "pvp", "versus" },
                    FlatStyle = FlatStyle.Flat
                };
                dgvUnlocks.Columns.Add(colType);

                // Version column (Numeric)
                var colVersion = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Version",
                    HeaderText = "Version",
                    ReadOnly = false
                };
                dgvUnlocks.Columns.Add(colVersion);

                // Area column (Numeric)
                var colArea = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Area",
                    HeaderText = "Area",
                    ReadOnly = false
                };
                dgvUnlocks.Columns.Add(colArea);

                // Amount column (Numeric) - NOVO
                var colAmount = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Amount",
                    HeaderText = "Amount",
                    ReadOnly = false
                };
                dgvUnlocks.Columns.Add(colAmount);

                // To column - make it consistent with List column
                var colTo = new DataGridViewTextBoxColumn
                {
                    HeaderText = "To",
                    ReadOnly = true,
                    Name = "To"
                };
                dgvUnlocks.Columns.Add(colTo);

                // List column - make it consistent with To column
                var colList = new DataGridViewTextBoxColumn
                {
                    HeaderText = "List",
                    ReadOnly = true,
                    Name = "List"
                };
                dgvUnlocks.Columns.Add(colList);

                bindingSource = new BindingSource();
                dgvUnlocks.DataSource = bindingSource;

                // Add/Remove buttons
                btnAdd = new Button
                {
                    Text = Properties.Resources.Button_Add ?? "Add",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnAdd.Click += BtnAdd_Click;

                btnRemove = new Button
                {
                    Text = Properties.Resources.Button_Remove ?? "Remove",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnRemove.Click += BtnRemove_Click;

                // Layout for table and buttons
                var layout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 2,
                    ColumnCount = 1,
                    AutoSize = true
                };
                layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
                layout.Controls.Add(dgvUnlocks, 0, 0);

                var buttonPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    FlowDirection = FlowDirection.LeftToRight,
                    Height = 40
                };
                buttonPanel.Controls.Add(btnAdd);
                buttonPanel.Controls.Add(btnRemove);

                layout.Controls.Add(buttonPanel, 0, 1);

                this.Controls.Add(layout);

                dgvUnlocks.CellFormatting += DgvUnlocks_CellFormatting;
                dgvUnlocks.CellClick += DgvUnlocks_CellClick;
                dgvUnlocks.CellBeginEdit += DgvUnlocks_CellBeginEdit;
            }

            public void LoadUnlocks(System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock> unlocks, List<OmnimonModuleEditor.Models.Pet> pets)
            {
                this.unlocks = unlocks ?? new System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock>();
                this.pets = pets ?? new List<OmnimonModuleEditor.Models.Pet>();
                foreach (var u in this.unlocks)
                {
                    u.To = u.To ?? new List<string>();
                    u.List = u.List ?? new List<string>();
                }
                bindingSource.DataSource = this.unlocks;
                dgvUnlocks.Refresh();
            }

            public System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock> GetUnlocks()
            {
                var result = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock>();
                foreach (DataGridViewRow row in dgvUnlocks.Rows)
                {
                    if (row.DataBoundItem is OmnimonModuleEditor.Models.Unlock unlock)
                    {
                        result.Add(new OmnimonModuleEditor.Models.Unlock
                        {
                            Name = unlock.Name,
                            Label = unlock.Label,
                            Type = unlock.Type,
                            Version = unlock.Version,
                            Area = unlock.Area,
                            Amount = unlock.Amount,
                            To = unlock.To ?? new List<string>(),
                            List = unlock.List ?? new List<string>()
                        });
                    }
                }
                return result;
            }

            private void BtnAdd_Click(object sender, EventArgs e)
            {
                if (unlocks == null)
                    unlocks = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Unlock>();

                var unlock = new OmnimonModuleEditor.Models.Unlock
                {
                    Name = "new_unlock",
                    Label = "New Unlock",
                    Type = "egg",
                    Version = 0,
                    Area = 0,
                    To = new System.Collections.Generic.List<string>(),
                    Amount = 1, // valor padr�o
                    List = new System.Collections.Generic.List<string>()
                };
                unlocks.Add(unlock);

                // Atualize o DataSource explicitamente
                bindingSource.DataSource = null;
                bindingSource.DataSource = unlocks;
                bindingSource.ResetBindings(false);

                // Seleciona a nova linha
                if (dgvUnlocks.Rows.Count > 0)
                    dgvUnlocks.CurrentCell = dgvUnlocks.Rows[dgvUnlocks.Rows.Count - 1].Cells[0];
            }

            private void BtnRemove_Click(object sender, EventArgs e)
            {
                if (dgvUnlocks.CurrentRow != null && dgvUnlocks.CurrentRow.Index >= 0 && dgvUnlocks.CurrentRow.Index < unlocks.Count)
                {
                    unlocks.RemoveAt(dgvUnlocks.CurrentRow.Index);
                    bindingSource.ResetBindings(false);
                }
            }

            private void DgvUnlocks_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
            {
                if (dgvUnlocks.Columns[e.ColumnIndex].Name == "To")
                {
                    var unlock = dgvUnlocks.Rows[e.RowIndex].DataBoundItem as OmnimonModuleEditor.Models.Unlock;
                    if (unlock != null && unlock.To != null && unlock.To.Count > 0)
                    {
                        e.Value = string.Join(", ", unlock.To);
                    }
                    else
                    {
                        e.Value = "";
                    }
                }
                else if (dgvUnlocks.Columns[e.ColumnIndex].Name == "List")
                {
                    var unlock = dgvUnlocks.Rows[e.RowIndex].DataBoundItem as OmnimonModuleEditor.Models.Unlock;
                    if (unlock != null && unlock.List != null && unlock.List.Count > 0)
                    {
                        e.Value = string.Join(", ", unlock.List);
                    }
                    else
                    {
                        e.Value = "";
                    }
                }
            }

            private void DgvUnlocks_CellClick(object sender, DataGridViewCellEventArgs e)
            {
                if (e.RowIndex >= 0 && e.ColumnIndex >= 0)
                {
                    var unlock = dgvUnlocks.Rows[e.RowIndex].DataBoundItem as OmnimonModuleEditor.Models.Unlock;
                    if (unlock == null) return;

                    // Handle 'To' column for evolution/digidex
                    if (dgvUnlocks.Columns[e.ColumnIndex].Name == "To" && (unlock.Type == "evolution" || unlock.Type == "digidex"))
                    {
                        using (var form = new PetListEditorForm(unlock.To ?? new List<string>(), pets))
                        {
                            if (form.ShowDialog() == DialogResult.OK)
                            {
                                unlock.To = form.SelectedPets ?? new List<string>();
                                dgvUnlocks.InvalidateRow(e.RowIndex);
                            }
                        }
                    }
                    // Handle 'List' column for group unlocks
                    else if (dgvUnlocks.Columns[e.ColumnIndex].Name == "List" && unlock.Type == "group")
                    {
                        using (var form = new GroupUnlockEditorForm(unlock.List ?? new List<string>(), unlocks.Where(u => u.Type != "group").ToList()))
                        {
                            if (form.ShowDialog() == DialogResult.OK)
                            {
                                unlock.List = form.SelectedUnlocks ?? new List<string>();
                                dgvUnlocks.InvalidateRow(e.RowIndex);
                            }
                        }
                    }
                }
            }

            private void DgvUnlocks_CellBeginEdit(object sender, DataGridViewCellCancelEventArgs e)
            {
                // Cancel editing for To and List columns since they use forms
                if (dgvUnlocks.Columns[e.ColumnIndex].Name == "To" || dgvUnlocks.Columns[e.ColumnIndex].Name == "List")
                {
                    e.Cancel = true;
                }
            }
        }

        // Backgrounds tab panel
        private class BackgroundsPanel : Panel
        {
            private DataGridView dgvBackgrounds;
            private BindingSource bindingSource;
            private Button btnAdd;
            private Button btnRemove;
            private Button btnRefresh; // Adicione o campo
            private Button btnImport; // Adicione o campo
            private System.Collections.Generic.List<OmnimonModuleEditor.Models.Background> backgrounds;
            private string modulePath;

            public BackgroundsPanel()
            {
                this.Dock = DockStyle.Fill;
                this.BackColor = SystemColors.Control;

                dgvBackgrounds = new DataGridView
                {
                    Dock = DockStyle.Fill,
                    AutoGenerateColumns = false,
                    AllowUserToAddRows = false,
                    AllowUserToDeleteRows = false,
                    RowHeadersVisible = false,
                    SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                    MultiSelect = false,
                    ReadOnly = false,
                    AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
                };

                // Name column
                var colName = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Name",
                    HeaderText = "Name",
                    ReadOnly = false
                };
                dgvBackgrounds.Columns.Add(colName);

                // Label column
                var colLabel = new DataGridViewTextBoxColumn
                {
                    DataPropertyName = "Label",
                    HeaderText = "Label",
                    ReadOnly = false
                };
                dgvBackgrounds.Columns.Add(colLabel);

                // DayNight column
                var colDayNight = new DataGridViewCheckBoxColumn
                {
                    DataPropertyName = "DayNight",
                    HeaderText = "DayNight",
                    ReadOnly = false
                };
                dgvBackgrounds.Columns.Add(colDayNight);

                // HiRes column (validation, not editable)
                var colHiRes = new DataGridViewTextBoxColumn
                {
                    Name = "HiRes",
                    HeaderText = "HiRes",
                    ReadOnly = true
                };
                dgvBackgrounds.Columns.Add(colHiRes);

                // Valid column (validation, not editable)
                var colValid = new DataGridViewTextBoxColumn
                {
                    Name = "Valid",
                    HeaderText = "Valid",
                    ReadOnly = true
                };
                dgvBackgrounds.Columns.Add(colValid);

                dgvBackgrounds.CellFormatting += DgvBackgrounds_CellFormatting;

                bindingSource = new BindingSource();
                dgvBackgrounds.DataSource = bindingSource;

                // Add/Remove/Refresh/Import buttons
                btnAdd = new Button
                {
                    Text = Properties.Resources.Button_Add ?? "Add",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnAdd.Click += BtnAdd_Click;

                btnRemove = new Button
                {
                    Text = Properties.Resources.Button_Remove ?? "Remove",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnRemove.Click += BtnRemove_Click;

                btnRefresh = new Button
                {
                    Text = Properties.Resources.Button_Refresh ?? "Refresh",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnRefresh.Click += (s, e) => ValidateAll();

                btnImport = new Button
                {
                    Text = Properties.Resources.Button_Import ?? "Import",
                    Width = 80,
                    Height = 30,
                    Anchor = AnchorStyles.Left
                };
                btnImport.Click += BtnImport_Click;

                // Layout for table and buttons
                var layout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 2,
                    ColumnCount = 1,
                    AutoSize = true
                };
                layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
                layout.Controls.Add(dgvBackgrounds, 0, 0);

                var buttonPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    FlowDirection = FlowDirection.LeftToRight,
                    Height = 40
                };
                buttonPanel.Controls.Add(btnAdd);
                buttonPanel.Controls.Add(btnRemove);
                buttonPanel.Controls.Add(btnRefresh);
                buttonPanel.Controls.Add(btnImport); // Adicione o bot�o de importa��o

                layout.Controls.Add(buttonPanel, 0, 1);

                this.Controls.Add(layout);

                backgrounds = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>();
            }

            /// <summary>
            /// Call this to load the backgrounds list from the module.
            /// </summary>
            public void LoadBackgrounds(System.Collections.Generic.List<OmnimonModuleEditor.Models.Background> backgrounds, string modulePath = null)
            {
                this.backgrounds = backgrounds ?? new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>();
                this.modulePath = modulePath;
                bindingSource.DataSource = this.backgrounds;
                dgvBackgrounds.Refresh();
                ValidateAll();
            }

            public System.Collections.Generic.List<OmnimonModuleEditor.Models.Background> GetBackgrounds()
            {
                // Always return a new list to avoid binding issues
                return backgrounds != null
                    ? new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>(backgrounds)
                    : new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>();
            }

            private void BtnAdd_Click(object sender, EventArgs e)
            {
                if (backgrounds == null)
                    backgrounds = new System.Collections.Generic.List<OmnimonModuleEditor.Models.Background>();

                var bg = new OmnimonModuleEditor.Models.Background
                {
                    Name = "new_bg",
                    Label = "New Background",
                    DayNight = false
                };
                backgrounds.Add(bg);
                bindingSource.ResetBindings(false);
                ValidateAll();

                // Select the new row for user convenience
                if (dgvBackgrounds.Rows.Count > 0)
                    dgvBackgrounds.CurrentCell = dgvBackgrounds.Rows[dgvBackgrounds.Rows.Count - 1].Cells[0];
            }

            private void BtnRemove_Click(object sender, EventArgs e)
            {
                if (dgvBackgrounds.CurrentRow != null && dgvBackgrounds.CurrentRow.Index >= 0 && dgvBackgrounds.CurrentRow.Index < backgrounds.Count)
                {
                    backgrounds.RemoveAt(dgvBackgrounds.CurrentRow.Index);
                    bindingSource.ResetBindings(false);
                    ValidateAll();
                }
            }

            // This event will color the "Valid" cell and set its value to YES/NO
            private void DgvBackgrounds_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
            {
                var bg = dgvBackgrounds.Rows[e.RowIndex].DataBoundItem as OmnimonModuleEditor.Models.Background;
                if (bg == null) return;

                if (dgvBackgrounds.Columns[e.ColumnIndex].Name == "Valid")
                {
                    bool valid = ValidateBackground(bg);
                    e.Value = valid ? "YES" : "NO";
                    e.CellStyle.ForeColor = Color.White;
                    e.CellStyle.BackColor = valid ? Color.Green : Color.Red;
                }
                else if (dgvBackgrounds.Columns[e.ColumnIndex].Name == "HiRes")
                {
                    bool hiRes = ValidateHiRes(bg);
                    e.Value = hiRes ? "YES" : "NO";
                    e.CellStyle.ForeColor = Color.White;
                    e.CellStyle.BackColor = hiRes ? Color.Green : Color.Red;
                }
            }

            private void ValidateAll()
            {
                dgvBackgrounds.Refresh();
            }

            private bool ValidateBackground(OmnimonModuleEditor.Models.Background bg)
            {
                if (string.IsNullOrWhiteSpace(modulePath) || string.IsNullOrWhiteSpace(bg.Name))
                    return false;

                string backgroundsDir = Path.Combine(modulePath, "backgrounds");
                if (!Directory.Exists(backgroundsDir))
                {
                    try { Directory.CreateDirectory(backgroundsDir); }
                    catch { return false; }
                }

                if (bg.DayNight)
                {
                    // Must have all three files
                    string[] suffixes = { "day", "dusk", "night" };
                    foreach (var suffix in suffixes)
                    {
                        string file = Path.Combine(backgroundsDir, $"bg_{bg.Name}_{suffix}.png");
                        if (!File.Exists(file))
                            return false;
                    }
                    return true;
                }
                else
                {
                    // Must have single file
                    string file = Path.Combine(backgroundsDir, $"bg_{bg.Name}.png");
                    return File.Exists(file);
                }
            }

            // L�gica do bot�o Import
            private void BtnImport_Click(object sender, EventArgs e)
            {
                if (string.IsNullOrWhiteSpace(modulePath))
                    return;

                string backgroundsDir = Path.Combine(modulePath, "backgrounds");
                if (!Directory.Exists(backgroundsDir))
                    Directory.CreateDirectory(backgroundsDir);

                using (var dialog = new OpenFileDialog())
                {
                    dialog.Title = Properties.Resources.BackgroundsPanel_ImportTitle ?? "Select background PNG";
                    dialog.Filter = "PNG files (*.png)|*.png";
                    dialog.InitialDirectory = backgroundsDir;
                    dialog.Multiselect = false;
                    if (dialog.ShowDialog() == DialogResult.OK)
                    {
                        string fileName = Path.GetFileNameWithoutExtension(dialog.FileName);

                        // Filtragem do nome
                        string name = fileName;
                        if (name.StartsWith("bg_")) name = name.Substring(3);
                        name = name.Replace("_high", "");
                        bool isDayNight = false;
                        foreach (var suffix in new[] { "_day", "_dusk", "_night" })
                        {
                            if (name.EndsWith(suffix))
                            {
                                name = name.Substring(0, name.Length - suffix.Length);
                                isDayNight = true;
                            }
                        }

                        // Verifica se j� existe
                        if (backgrounds.Any(b => b.Name == name))
                        {
                            MessageBox.Show(
                                string.Format(Properties.Resources.BackgroundsPanel_AlreadyExists ?? "Background \"{0}\" already exists.", name),
                                Properties.Resources.Warning ?? "Warning",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Warning
                            );
                            return;
                        }

                        // Adiciona � lista
                        var bg = new OmnimonModuleEditor.Models.Background
                        {
                            Name = name,
                            Label = name,
                            DayNight = isDayNight
                        };
                        backgrounds.Add(bg);
                        bindingSource.ResetBindings(false);
                        ValidateAll();

                        // Seleciona o novo
                        if (dgvBackgrounds.Rows.Count > 0)
                            dgvBackgrounds.CurrentCell = dgvBackgrounds.Rows[dgvBackgrounds.Rows.Count - 1].Cells[0];
                    }
                }
            }

            // Novo m�todo para valida��o HiRes:
            private bool ValidateHiRes(OmnimonModuleEditor.Models.Background bg)
            {
                if (string.IsNullOrWhiteSpace(modulePath) || string.IsNullOrWhiteSpace(bg.Name))
                    return false;

                string backgroundsDir = Path.Combine(modulePath, "backgrounds");
                if (!Directory.Exists(backgroundsDir))
                    return false;

                if (bg.DayNight)
                {
                    // Checa bg_bgname_day_high.png
                    string hiResDay = Path.Combine(backgroundsDir, $"bg_{bg.Name}_day_high.png");
                    if (File.Exists(hiResDay))
                        return true;
                }
                // Checa bg_bgname_high.png
                string hiRes = Path.Combine(backgroundsDir, $"bg_{bg.Name}_high.png");
                return File.Exists(hiRes);
            }
        }

        // Pet List Editor Form class
        public class PetListEditorForm : Form
        {
            private CheckedListBox checkedListBox;
            private Button btnOK;
            private Button btnCancel;
            private Button btnSelectAll;
            private Button btnSelectNone;
        
            public List<string> SelectedPets { get; private set; }

            public PetListEditorForm(List<string> currentSelection, List<OmnimonModuleEditor.Models.Pet> allPets)
            {
                InitializeComponent();
                PopulatePets(allPets, currentSelection);
            }

            private void InitializeComponent()
            {
                this.Text = "Edit Pet List";
                this.Size = new Size(450, 550);
                this.StartPosition = FormStartPosition.CenterParent;
                this.FormBorderStyle = FormBorderStyle.FixedDialog;
                this.MaximizeBox = false;
                this.MinimizeBox = false;

                var mainLayout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 3,
                    ColumnCount = 1,
                    Padding = new Padding(15)
                };
                mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                mainLayout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
                mainLayout.RowStyles.Add(new RowStyle(SizeType.AutoSize));

                var titleLabel = new Label
                {
                    Text = "Select pets for this unlock:",
                    Dock = DockStyle.Fill,
                    AutoSize = true,
                    Font = new Font(SystemFonts.DefaultFont, FontStyle.Bold),
                    Padding = new Padding(0, 0, 0, 10)
                };
                mainLayout.Controls.Add(titleLabel, 0, 0);

                checkedListBox = new CheckedListBox
                {
                    Dock = DockStyle.Fill,
                    CheckOnClick = true,
                    IntegralHeight = false,
                    AutoSize = false
                };
                mainLayout.Controls.Add(checkedListBox, 0, 1);

                // Buttons panel
                var buttonPanel = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 1,
                    ColumnCount = 4,
                    Height = 40,
                    Padding = new Padding(0, 10, 0, 0)
                };
                buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
                buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
                buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
                buttonPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));

                btnSelectAll = new Button
                {
                    Text = "Select All",
                    Dock = DockStyle.Fill,
                    Margin = new Padding(0, 0, 5, 0)
                };
                btnSelectAll.Click += (s, e) =>
                {
                    for (int i = 0; i < checkedListBox.Items.Count; i++)
                        checkedListBox.SetItemChecked(i, true);
                };

                btnSelectNone = new Button
                {
                    Text = "Select None",
                    Dock = DockStyle.Fill,
                    Margin = new Padding(0, 0, 5, 0)
                };
                btnSelectNone.Click += (s, e) =>
                {
                    for (int i = 0; i < checkedListBox.Items.Count; i++)
                        checkedListBox.SetItemChecked(i, false);
                };

                btnOK = new Button
                {
                    Text = "OK",
                    DialogResult = DialogResult.OK,
                    Dock = DockStyle.Fill,
                    Margin = new Padding(0, 0, 5, 0)
                };

                btnCancel = new Button
                {
                    Text = "Cancel",
                    DialogResult = DialogResult.Cancel,
                    Dock = DockStyle.Fill
                };

                buttonPanel.Controls.Add(btnSelectAll, 0, 0);
                buttonPanel.Controls.Add(btnSelectNone, 1, 0);
                buttonPanel.Controls.Add(btnOK, 2, 0);
                buttonPanel.Controls.Add(btnCancel, 3, 0);

                mainLayout.Controls.Add(buttonPanel, 0, 2);

                this.Controls.Add(mainLayout);
                this.AcceptButton = btnOK;
                this.CancelButton = btnCancel;

                btnOK.Click += BtnOK_Click;
            }

            private void PopulatePets(List<OmnimonModuleEditor.Models.Pet> allPets, List<string> currentSelection)
            {
                checkedListBox.Items.Clear();
                
                if (allPets != null)
                {
                    foreach (var pet in allPets)
                    {
                        string displayText = $"{pet.Name} (Stage {pet.Stage})";
                        var petItem = new PetItem { Pet = pet, DisplayText = displayText };
                        int index = checkedListBox.Items.Add(petItem);
                        
                        // Check if this pet is in the current selection
                        if (currentSelection != null && currentSelection.Contains(pet.Name))
                        {
                            checkedListBox.SetItemChecked(index, true);
                        }
                    }
                }
            }

            private void BtnOK_Click(object sender, EventArgs e)
            {
                SelectedPets = new List<string>();
                
                foreach (var item in checkedListBox.CheckedItems)
                {
                    if (item is PetItem petItem)
                    {
                        SelectedPets.Add(petItem.Pet.Name);
                    }
                }
            }

            private class PetItem
            {
                public OmnimonModuleEditor.Models.Pet Pet { get; set; }
                public string DisplayText { get; set; }

                public override string ToString()
                {
                    return DisplayText;
                }
            }
        }

        #endregion
    }
}