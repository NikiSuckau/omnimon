using OmnimonModuleEditor.Models;
using OmnimonModuleEditor.Properties;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

/// <summary>
/// Dialog for editing evolution criteria.
/// </summary>
public class EvolutionCriteriaForm : Form
{
    private Evolution evolution;
    private List<string> items;

    // Input fields
    private NumericUpDown[] numConditionHearts = new NumericUpDown[2];
    private NumericUpDown[] numTraining = new NumericUpDown[2];
    private NumericUpDown[] numBattles = new NumericUpDown[2];
    private NumericUpDown[] numWinRatio = new NumericUpDown[2];
    private NumericUpDown[] numWinCount = new NumericUpDown[2]; // New field
    private NumericUpDown[] numMistakes = new NumericUpDown[2];
    private NumericUpDown[] numLevel = new NumericUpDown[2];
    private NumericUpDown[] numOverfeed = new NumericUpDown[2];
    private NumericUpDown[] numSleepDisturbances = new NumericUpDown[2];
    private NumericUpDown[] numStage5 = new NumericUpDown[2];
    private NumericUpDown[] numStage6 = new NumericUpDown[2]; // New field
    private NumericUpDown[] numStage7 = new NumericUpDown[2]; // New field
    private NumericUpDown[] numStage8 = new NumericUpDown[2]; // New field
    private NumericUpDown[] numTrophies = new NumericUpDown[2]; // New field
    private NumericUpDown[] numVitalValues = new NumericUpDown[2]; // New field
    private NumericUpDown[] numWeigth = new NumericUpDown[2]; // New field
    private NumericUpDown[] numQuestsCompleted = new NumericUpDown[2]; // New field
    private NumericUpDown[] numPvp = new NumericUpDown[2]; // New field

    private NumericUpDown numArea;
    private NumericUpDown numStage;
    private NumericUpDown numVersion;
    private ComboBox cmbAttribute;
    private TextBox txtJogress;
    private CheckBox chkSpecialEncounter;
    private ComboBox cmbItem;

    private Button btnSave;
    private Button btnCancel;
    private Button btnCopy;
    private Button btnPaste;

    // Adicione o campo privado
    private CheckBox chkJogressPrefix;

    // Adicione os campos para time_range
    private MaskedTextBox[] txtTimeRange = new MaskedTextBox[2];

    /// <summary>
    /// Initializes a new instance of the <see cref="EvolutionCriteriaForm"/> class.
    /// </summary>
    public EvolutionCriteriaForm(Evolution evo, List<Item> items)
    {
        this.evolution = evo;
        this.items = GetItemNames(items);

        InitializeComponent();
        LoadEvolution();
    }

    /// <summary>
    /// Gets the list of item names from the item list.
    /// </summary>
    private List<string> GetItemNames(List<Item> items)
    {
        if (items == null)
            return new List<string>();
        return items.Select(i => i.Name).ToList();
    }

    /// <summary>
    /// Initializes the layout and UI controls.
    /// </summary>
    private void InitializeComponent()
    {
        this.Text = Resources.EvolutionCriteriaForm_Title;
        this.Size = new Size(440, 720); // Increased height for new fields
        this.FormBorderStyle = FormBorderStyle.FixedDialog;
        this.MaximizeBox = false;
        this.MinimizeBox = false;
        this.StartPosition = FormStartPosition.CenterParent;

        var scrollPanel = new Panel
        {
            Dock = DockStyle.Fill,
            AutoScroll = true,
            Padding = new Padding(8)
        };

        var layout = new TableLayoutPanel
        {
            Dock = DockStyle.Top,
            ColumnCount = 2,
            AutoSize = true
        };
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 150));
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));

        int row = 0;

        void AddLabel(string text)
        {
            var lbl = new Label
            {
                Text = text,
                Anchor = AnchorStyles.Left,
                AutoSize = true,
                Font = new Font("Segoe UI", 8),
                Margin = new Padding(0, 6, 0, 0)
            };
            layout.Controls.Add(lbl, 0, row);
        }

        void AddControl(Control control)
        {
            control.Margin = new Padding(0, 4, 0, 0);
            layout.Controls.Add(control, 1, row);
            row++;
        }

        void AddRange(string label, NumericUpDown[] controls, int min, int max)
        {
            AddLabel(label);
            var rangePanel = new FlowLayoutPanel
            {
                FlowDirection = FlowDirection.LeftToRight,
                AutoSize = true,
                WrapContents = false
            };
            controls[0] = new NumericUpDown { Minimum = min, Maximum = max, Width = 60 };
            controls[1] = new NumericUpDown { Minimum = min, Maximum = max, Width = 60 };
            rangePanel.Controls.Add(controls[0]);
            rangePanel.Controls.Add(new Label { Text = Resources.EvolutionCriteriaForm_LabelTo, AutoSize = true, TextAlign = ContentAlignment.MiddleCenter, Padding = new Padding(4, 6, 4, 0) });
            rangePanel.Controls.Add(controls[1]);
            AddControl(rangePanel);
        }

        AddRange(Resources.EvolutionCriteriaForm_LabelConditionHearts, numConditionHearts, -1, 999999);
        AddRange(Resources.EvolutionCriteriaForm_LabelTraining, numTraining, -1, 999999);
        AddRange(Resources.EvolutionCriteriaForm_LabelBattles, numBattles, -1, 999999);
        AddRange(Resources.EvolutionCriteriaForm_LabelWinRatio, numWinRatio, -1, 100);
        AddRange("Win Count:", numWinCount, -1, 999999); // New field
        AddRange(Resources.EvolutionCriteriaForm_LabelMistakes, numMistakes, -1, 999999);
        AddRange(Resources.EvolutionCriteriaForm_LabelLevel, numLevel, -1, 10);
        AddRange(Resources.EvolutionCriteriaForm_LabelOverfeed, numOverfeed, -1, 999999);
        AddRange(Resources.EvolutionCriteriaForm_LabelSleepDisturbances, numSleepDisturbances, -1, 999999);

        AddLabel(Resources.EvolutionCriteriaForm_LabelArea);
        numArea = new NumericUpDown { Minimum = 0, Maximum = 999999, Width = 60 };
        AddControl(numArea);

        AddLabel(Resources.EvolutionCriteriaForm_LabelJogressName);
        txtJogress = new TextBox { Width = 120 };
        txtJogress.TextChanged += (s, e) =>
        {
            bool enabled = !string.IsNullOrWhiteSpace(txtJogress.Text);
            numStage.Enabled = enabled;
            numVersion.Enabled = enabled;
            cmbAttribute.Enabled = enabled;
        };
        AddControl(txtJogress);

        AddLabel("Jogress Prefix");
        chkJogressPrefix = new CheckBox();
        AddControl(chkJogressPrefix);

        AddLabel(Resources.EvolutionCriteriaForm_LabelStageJogress);
        numStage = new NumericUpDown { Minimum = 0, Maximum = 999999, Width = 60 };
        AddControl(numStage);

        AddLabel(Resources.EvolutionCriteriaForm_LabelVersionJogress);
        numVersion = new NumericUpDown { Minimum = 0, Maximum = 999999, Width = 60 };
        AddControl(numVersion);

        AddLabel(Resources.EvolutionCriteriaForm_LabelAttributeJogress);
        cmbAttribute = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 80 };
        cmbAttribute.Items.AddRange(new object[] { "", "Da", "Vi", "Va", "Free" });
        AddControl(cmbAttribute);

        AddLabel(Resources.EvolutionCriteriaForm_LabelSpecialEncounter);
        chkSpecialEncounter = new CheckBox();
        AddControl(chkSpecialEncounter);

        AddRange(Resources.EvolutionCriteriaForm_LabelStage5, numStage5, -1, 999999);
        AddRange("Stage-6:", numStage6, -1, 999999); // New field
        AddRange("Stage-7:", numStage7, -1, 999999); // New field
        AddRange("Stage-8:", numStage8, -1, 999999); // New field
        AddRange("Trophies:", numTrophies, -1, 999999); // New field
        AddRange("Vital Values:", numVitalValues, -1, 999999); // New field
        AddRange("Weight:", numWeigth, -1, 100); // New field
        AddRange("Quests Completed:", numQuestsCompleted, -1, 100); // New field
        AddRange("PVP:", numPvp, -1, 999999); // New field

        AddLabel(Resources.EvolutionCriteriaForm_LabelItem);
        cmbItem = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 150 };
        cmbItem.Items.Add(""); // none
        foreach (var item in items)
            cmbItem.Items.Add(item);
        AddControl(cmbItem);

        // Adicione os campos para time_range
        AddLabel("Time Range");
        var timePanel = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.LeftToRight,
            AutoSize = true,
            WrapContents = false
        };
        txtTimeRange[0] = new MaskedTextBox { Mask = "00:00", Width = 50 };
        txtTimeRange[1] = new MaskedTextBox { Mask = "00:00", Width = 50 };
        timePanel.Controls.Add(txtTimeRange[0]);
        timePanel.Controls.Add(new Label { Text = "to", AutoSize = true, TextAlign = ContentAlignment.MiddleCenter, Padding = new Padding(4, 6, 4, 0) });
        timePanel.Controls.Add(txtTimeRange[1]);
        AddControl(timePanel);

        // Buttons
        btnSave = new Button { Text = Resources.Button_Save, Width = 90, DialogResult = DialogResult.OK };
        btnCancel = new Button { Text = Resources.Button_Cancel, Width = 90, DialogResult = DialogResult.Cancel };
        btnCopy = new Button { Text = Resources.Button_Copy, Width = 90 };
        btnPaste = new Button { Text = Resources.Button_Paste, Width = 90 };

        btnCopy.Click += (s, e) =>
        {
            try
            {
                var evoCopy = new Evolution();
                SaveToEvolution();
                CopyEvolutionFields(evolution, evoCopy);
                string json = JsonSerializer.Serialize(evoCopy, new JsonSerializerOptions { WriteIndented = false });
                Clipboard.SetText(json);
            }
            catch (Exception ex)
            {
                MessageBox.Show(Resources.EvolutionCriteriaForm_ErrorCopy + ex.Message, Resources.Error, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        };

        btnPaste.Click += (s, e) =>
        {
            try
            {
                if (Clipboard.ContainsText())
                {
                    string json = Clipboard.GetText();
                    var evoPaste = JsonSerializer.Deserialize<Evolution>(json);
                    if (evoPaste != null)
                    {
                        string currentTo = evolution.To;
                        CopyEvolutionFields(evoPaste, evolution);
                        evolution.To = currentTo;
                        LoadEvolution();
                    }
                    else
                    {
                        MessageBox.Show(Resources.EvolutionCriteriaForm_ErrorInvalidClipboard, Resources.Error, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(Resources.EvolutionCriteriaForm_ErrorPaste + ex.Message, Resources.Error, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        };

        var buttonPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Bottom,
            FlowDirection = FlowDirection.RightToLeft,
            Height = 50,
            Padding = new Padding(0, 10, 8, 8)
        };
        buttonPanel.Controls.Add(btnCancel);
        buttonPanel.Controls.Add(btnSave);
        buttonPanel.Controls.Add(btnPaste);
        buttonPanel.Controls.Add(btnCopy);

        btnSave.Click += (s, e) =>
        {
            if (SaveToEvolution())
                this.DialogResult = DialogResult.OK;
        };

        btnCancel.Click += (s, e) => this.DialogResult = DialogResult.Cancel;

        scrollPanel.Controls.Add(layout);
        this.Controls.Add(scrollPanel);
        this.Controls.Add(buttonPanel);
    }

    /// <summary>
    /// Copies all fields from one Evolution object to another (deep copy).
    /// </summary>
    private void CopyEvolutionFields(Evolution src, Evolution dest)
    {
        dest.To = src.To;
        dest.ConditionHearts = src.ConditionHearts != null ? (int[])src.ConditionHearts.Clone() : null;
        dest.Training = src.Training != null ? (int[])src.Training.Clone() : null;
        dest.Battles = src.Battles != null ? (int[])src.Battles.Clone() : null;
        dest.WinRatio = src.WinRatio != null ? (int[])src.WinRatio.Clone() : null;
        dest.WinCount = src.WinCount != null ? (int[])src.WinCount.Clone() : null; // New field
        dest.Mistakes = src.Mistakes != null ? (int[])src.Mistakes.Clone() : null;
        dest.Level = src.Level != null ? (int[])src.Level.Clone() : null;
        dest.Overfeed = src.Overfeed != null ? (int[])src.Overfeed.Clone() : null;
        dest.SleepDisturbances = src.SleepDisturbances != null ? (int[])src.SleepDisturbances.Clone() : null;
        dest.Area = src.Area;
        dest.Stage = src.Stage;
        dest.Version = src.Version;
        dest.Attribute = src.Attribute;
        dest.Jogress = src.Jogress;
        dest.SpecialEncounter = src.SpecialEncounter;
        dest.Stage5 = src.Stage5 != null ? (int[])src.Stage5.Clone() : null;
        dest.Stage6 = src.Stage6 != null ? (int[])src.Stage6.Clone() : null; // New field
        dest.Stage7 = src.Stage7 != null ? (int[])src.Stage7.Clone() : null; // New field
        dest.Stage8 = src.Stage8 != null ? (int[])src.Stage8.Clone() : null; // New field
        dest.Item = src.Item;
        dest.JogressPrefix = src.JogressPrefix;
        dest.TimeRange = src.TimeRange != null ? (string[])src.TimeRange.Clone() : null;
        dest.Trophies = src.Trophies != null ? (int[])src.Trophies.Clone() : null; // New field
        dest.VitalValues = src.VitalValues != null ? (int[])src.VitalValues.Clone() : null; // New field
        dest.Weigth = src.Weigth != null ? (int[])src.Weigth.Clone() : null; // New field
        dest.QuestsCompleted = src.QuestsCompleted != null ? (int[])src.QuestsCompleted.Clone() : null; // New field
        dest.Pvp = src.Pvp != null ? (int[])src.Pvp.Clone() : null; // New field
    }

    /// <summary>
    /// Loads the evolution data into the form fields.
    /// </summary>
    private void LoadEvolution()
    {
        void SetRange(NumericUpDown[] ctrls, int[] val)
        {
            ctrls[0].Value = val != null && val.Length > 0 ? val[0] : -1;
            ctrls[1].Value = val != null && val.Length > 1 ? val[1] : -1;
        }
        SetRange(numConditionHearts, evolution.ConditionHearts);
        SetRange(numTraining, evolution.Training);
        SetRange(numBattles, evolution.Battles);
        SetRange(numWinRatio, evolution.WinRatio);
        SetRange(numWinCount, evolution.WinCount); // New field
        SetRange(numMistakes, evolution.Mistakes);
        SetRange(numLevel, evolution.Level);
        SetRange(numOverfeed, evolution.Overfeed);
        SetRange(numSleepDisturbances, evolution.SleepDisturbances);
        SetRange(numStage5, evolution.Stage5);
        SetRange(numStage6, evolution.Stage6); // New field
        SetRange(numStage7, evolution.Stage7); // New field
        SetRange(numStage8, evolution.Stage8); // New field
        SetRange(numTrophies, evolution.Trophies); // New field
        SetRange(numVitalValues, evolution.VitalValues); // New field
        SetRange(numWeigth, evolution.Weigth); // New field
        SetRange(numQuestsCompleted, evolution.QuestsCompleted); // New field
        SetRange(numPvp, evolution.Pvp); // New field

        numArea.Value = evolution.Area ?? 0;
        numStage.Value = evolution.Stage ?? 0;
        numVersion.Value = evolution.Version ?? 0;
        cmbAttribute.SelectedItem = evolution.Attribute ?? "";
        txtJogress.Text = evolution.Jogress ?? "";
        chkSpecialEncounter.Checked = evolution.SpecialEncounter ?? false;
        cmbItem.SelectedItem = evolution.Item ?? "";

        // Carregue o valor:
        if (evolution.JogressPrefix == null)
        {
            evolution.JogressPrefix = false;
        }
        chkJogressPrefix.Checked = evolution.JogressPrefix ?? false;

        // Carregar time_range
        txtTimeRange[0].Text = (evolution.TimeRange != null && evolution.TimeRange.Length > 0) ? evolution.TimeRange[0] : "";
        txtTimeRange[1].Text = (evolution.TimeRange != null && evolution.TimeRange.Length > 1) ? evolution.TimeRange[1] : "";
    }

    /// <summary>
    /// Saves the form fields back to the evolution object.
    /// </summary>
    private bool SaveToEvolution()
    {
        int[] GetRange(NumericUpDown[] ctrls, int max)
        {
            int v0 = (int)ctrls[0].Value;
            int v1 = (int)ctrls[1].Value;
            if (v1 == -1) return null;
            if (v0 > max) v0 = max;
            if (v1 > max) v1 = max;
            if (v0 > v1) v0 = v1;
            if (v0 < 0) return new int[] { 0, v1 };
            return new int[] { v0, v1 };
        }

        evolution.ConditionHearts = GetRange(numConditionHearts, 999999);
        evolution.Training = GetRange(numTraining, 999999);
        evolution.Battles = GetRange(numBattles, 999999);
        evolution.WinRatio = GetRange(numWinRatio, 100);
        evolution.WinCount = GetRange(numWinCount, 999999); // New field
        evolution.Mistakes = GetRange(numMistakes, 999999);
        evolution.Level = GetRange(numLevel, 10);
        evolution.Overfeed = GetRange(numOverfeed, 999999);
        evolution.SleepDisturbances = GetRange(numSleepDisturbances, 999999);
        evolution.Stage5 = GetRange(numStage5, 999999);
        evolution.Stage6 = GetRange(numStage6, 999999); // New field
        evolution.Stage7 = GetRange(numStage7, 999999); // New field
        evolution.Stage8 = GetRange(numStage8, 999999); // New field
        evolution.Trophies = GetRange(numTrophies, 999999); // New field
        evolution.VitalValues = GetRange(numVitalValues, 999999); // New field
        evolution.Weigth = GetRange(numWeigth, 100); // New field
        evolution.QuestsCompleted = GetRange(numQuestsCompleted, 100); // New field
        evolution.Pvp = GetRange(numPvp, 999999); // New field

        evolution.Area = numArea.Value == 0 ? (int?)null : (int)numArea.Value;
        evolution.Stage = numStage.Value == 0 ? (int?)null : (int)numStage.Value;
        evolution.Version = numVersion.Value == 0 ? (int?)null : (int)numVersion.Value;
        evolution.Attribute = string.IsNullOrEmpty(cmbAttribute.Text) ? null : cmbAttribute.Text;
        evolution.Jogress = string.IsNullOrWhiteSpace(txtJogress.Text) ? null : txtJogress.Text;
        evolution.SpecialEncounter = chkSpecialEncounter.Checked ? true : (bool?)null;
        evolution.Item = string.IsNullOrEmpty(cmbItem.Text) ? null : cmbItem.Text;

        evolution.JogressPrefix = chkJogressPrefix.Checked ? true : (bool?)null;

        // Salvar time_range
        string t0 = txtTimeRange[0].Text.Trim();
        string t1 = txtTimeRange[1].Text.Trim();
        if (string.IsNullOrWhiteSpace(t0.Replace(":", "")) && string.IsNullOrWhiteSpace(t1.Replace(":", "")))
        {
            evolution.TimeRange = null;
        }
        else
        {
            evolution.TimeRange = new string[] { t0, t1 };
        }

        return true;
    }
}