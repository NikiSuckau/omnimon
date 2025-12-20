using OmnipetModuleEditor.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;

namespace OmnipetModuleEditor.Controls
{
    /// <summary>
    /// Dialog for adding a new battle enemy, allowing selection of version and pet.
    /// </summary>
    public class EnemyAddDialog : Form
    {
        /// <summary>
        /// Gets the selected version.
        /// </summary>
        public int SelectedVersion { get; private set; } = -1;

        /// <summary>
        /// Gets the selected pet, or null for custom.
        /// </summary>
        public Pet SelectedPet { get; private set; } = null;

        private ComboBox cmbVersion;
        private ComboBox cmbPet;
        private List<Pet> pets;

        /// <summary>
        /// Initializes a new instance of the <see cref="EnemyAddDialog"/> class.
        /// </summary>
        /// <param name="pets">List of available pets.</param>
        public EnemyAddDialog(List<Pet> pets)
        {
            this.pets = pets ?? new List<Pet>();
            InitializeComponent();
        }

        #region Initialization

        /// <summary>
        /// Initializes the dialog controls and layout.
        /// </summary>
        private void InitializeComponent()
        {
            this.Text = Properties.Resources.EnemyAddDialog_Title ?? "Add Enemy";
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.StartPosition = FormStartPosition.CenterParent;
            this.Width = 340;
            this.Height = 180;
            this.MaximizeBox = false;
            this.MinimizeBox = false;

            var lblVersion = new Label
            {
                Text = Properties.Resources.EnemyAddDialog_Label_Version ?? "Version:",
                Left = 16,
                Top = 20,
                Width = 80
            };
            cmbVersion = new ComboBox
            {
                Left = 100,
                Top = 16,
                Width = 200,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            var lblPet = new Label
            {
                Text = Properties.Resources.EnemyAddDialog_Label_Pet ?? "Pet:",
                Left = 16,
                Top = 60,
                Width = 80
            };
            cmbPet = new ComboBox
            {
                Left = 100,
                Top = 56,
                Width = 200,
                DropDownStyle = ComboBoxStyle.DropDownList
            };

            var btnOk = new Button
            {
                Text = Properties.Resources.Button_OK ?? "OK",
                DialogResult = DialogResult.OK,
                Left = 100,
                Top = 100,
                Width = 80
            };
            var btnCancel = new Button
            {
                Text = Properties.Resources.Button_Cancel ?? "Cancel",
                DialogResult = DialogResult.Cancel,
                Left = 200,
                Top = 100,
                Width = 80
            };

            this.Controls.Add(lblVersion);
            this.Controls.Add(cmbVersion);
            this.Controls.Add(lblPet);
            this.Controls.Add(cmbPet);
            this.Controls.Add(btnOk);
            this.Controls.Add(btnCancel);

            // Fill versions
            var versions = pets.Select(p => p.Version).Distinct().OrderBy(v => v).ToList();
            foreach (var v in versions)
                cmbVersion.Items.Add(string.Format(Properties.Resources.EnemyAddDialog_VersionItem ?? "Version {0}", v));
            if (cmbVersion.Items.Count > 0)
                cmbVersion.SelectedIndex = 0;

            cmbVersion.SelectedIndexChanged += (s, e) => UpdatePetList();
            UpdatePetList();

            btnOk.Click += BtnOk_Click;
        }

        #endregion

        #region Event Handlers

        /// <summary>
        /// Handles the OK button click event.
        /// </summary>
        private void BtnOk_Click(object sender, EventArgs e)
        {
            var versions = pets.Select(p => p.Version).Distinct().OrderBy(v => v).ToList();
            if (cmbVersion.SelectedIndex < 0) return;
            SelectedVersion = versions[cmbVersion.SelectedIndex];
            if (cmbPet.SelectedIndex == 0)
            {
                SelectedPet = null; // custom
            }
            else
            {
                var petsOfVersion = pets
                    .Where(p => p.Version == SelectedVersion)
                    .OrderBy(p => p.Stage)
                    .ThenBy(p => p.Name)
                    .ToList();
                SelectedPet = petsOfVersion[cmbPet.SelectedIndex - 1];
            }
        }

        #endregion

        #region Helpers

        /// <summary>
        /// Updates the pet list based on the selected version.
        /// </summary>
        private void UpdatePetList()
        {
            cmbPet.Items.Clear();
            cmbPet.Items.Add(Properties.Resources.EnemyAddDialog_PetItem_Custom ?? "Custom");
            if (cmbVersion.SelectedIndex < 0) return;
            var versions = pets.Select(p => p.Version).Distinct().OrderBy(v => v).ToList();
            int selectedVersion = versions[cmbVersion.SelectedIndex];
            var petsOfVersion = pets
                .Where(p => p.Version == selectedVersion)
                .OrderBy(p => p.Stage)
                .ThenBy(p => p.Name)
                .ToList();
            foreach (var pet in petsOfVersion)
                cmbPet.Items.Add(pet.Name);
            cmbPet.SelectedIndex = 0;
        }

        #endregion
    }
}