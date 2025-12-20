// OmnipetModuleEditor/Controls/PetListPanel.cs
using System.Drawing;
using System.Windows.Forms;

namespace OmnipetModuleEditor.Controls
{
    /// <summary>
    /// Panel that displays a list of pets and provides Add, Remove, Copy, and Paste buttons.
    /// </summary>
    public class PetListPanel : UserControl
    {
        /// <summary>
        /// Panel that contains the list of pet panels.
        /// </summary>
        public Panel PanelPetList { get; private set; }

        /// <summary>
        /// Button to add a new pet.
        /// </summary>
        public Button BtnAdd { get; private set; }

        /// <summary>
        /// Button to remove the selected pet.
        /// </summary>
        public Button BtnRemove { get; private set; }

        /// <summary>
        /// Button to copy the selected pet.
        /// </summary>
        public Button BtnCopy { get; private set; }

        /// <summary>
        /// Button to paste a copied pet.
        /// </summary>
        public Button BtnPaste { get; private set; }

        /// <summary>
        /// Initializes a new instance of the <see cref="PetListPanel"/> class.
        /// </summary>
        public PetListPanel()
        {
            InitializeComponent();
        }

        #region Initialization

        /// <summary>
        /// Initializes the layout and child controls.
        /// </summary>
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

            // Panel for the pet list
            PanelPetList = new Panel
            {
                Dock = DockStyle.Fill,
                AutoScroll = true,
                BackColor = Color.White
            };
            leftLayout.Controls.Add(PanelPetList, 0, 0);

            // Panel for the action buttons
            var panelButtons = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                Padding = new Padding(4),
                AutoSize = false,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                WrapContents = false
            };

            // Add button
            BtnAdd = new Button
            {
                Text = Properties.Resources.Button_Add ?? "Add",
                Width = 70,
                Margin = new Padding(0, 0, 4, 0)
            };

            // Remove button
            BtnRemove = new Button
            {
                Text = Properties.Resources.Button_Remove ?? "Remove",
                Width = 70,
                Margin = new Padding(0, 0, 4, 0)
            };

            // Copy button
            BtnCopy = new Button
            {
                Text = Properties.Resources.Button_Copy ?? "Copy",
                Width = 70,
                Margin = new Padding(0, 0, 4, 0)
            };

            // Paste button
            BtnPaste = new Button
            {
                Text = Properties.Resources.Button_Paste ?? "Paste",
                Width = 70,
                Margin = new Padding(0, 0, 4, 0)
            };

            panelButtons.Controls.AddRange(new Control[] { BtnAdd, BtnRemove, BtnCopy, BtnPaste });
            leftLayout.Controls.Add(panelButtons, 0, 1);

            this.Controls.Add(leftLayout);
        }

        #endregion
    }
}