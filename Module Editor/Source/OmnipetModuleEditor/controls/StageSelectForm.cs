using System;
using System.Drawing;
using System.Windows.Forms;

namespace OmnipetModuleEditor.Controls
{
    /// <summary>
    /// Popup dialog for selecting a pet stage.
    /// </summary>
    public class StageSelectForm : Form
    {
        /// <summary>
        /// Gets the selected stage index. Returns -1 if no selection was made.
        /// </summary>
        public int SelectedStage { get; private set; } = -1;

        private ComboBox comboStage;

        /// <summary>
        /// Initializes a new instance of the <see cref="StageSelectForm"/> class.
        /// </summary>
        public StageSelectForm()
        {
            InitializeComponent();
        }

        #region Initialization

        /// <summary>
        /// Initializes the form controls and layout.
        /// </summary>
        private void InitializeComponent()
        {
            this.Text = Properties.Resources.StageSelectForm_Title ?? "Select Stage";
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.StartPosition = FormStartPosition.CenterParent;
            this.Width = 260;
            this.Height = 140;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            var label = new Label
            {
                Text = Properties.Resources.StageSelectForm_Label ?? "Choose the stage for the new Pet:",
                Dock = DockStyle.Top,
                Height = 28,
                TextAlign = ContentAlignment.MiddleCenter
            };

            comboStage = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Dock = DockStyle.Top,
                Margin = new Padding(8),
                Height = 28
            };
            for (int i = 0; i <= 8; i++)
                comboStage.Items.Add(string.Format(Properties.Resources.StageSelectForm_StageItem ?? "Stage {0}", i));
            comboStage.SelectedIndex = 0;

            var btnOk = new Button
            {
                Text = Properties.Resources.Button_OK ?? "OK",
                DialogResult = DialogResult.OK,
                Dock = DockStyle.Bottom,
                Height = 32
            };

            this.Controls.Add(btnOk);
            this.Controls.Add(comboStage);
            this.Controls.Add(label);

            btnOk.Click += BtnOk_Click;
        }

        #endregion

        #region Event Handlers

        /// <summary>
        /// Handles the OK button click event.
        /// </summary>
        private void BtnOk_Click(object sender, EventArgs e)
        {
            SelectedStage = comboStage.SelectedIndex;
            this.DialogResult = DialogResult.OK;
            this.Close();
        }

        #endregion
    }
}