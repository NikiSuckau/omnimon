using Microsoft.VisualBasic;
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;

namespace OmnipetModuleEditor
{
    /// <summary>
    /// Form for selecting, creating, editing, and removing module folders.
    /// </summary>
    public partial class ModuleSelectorForm : Form
    {
        private System.Windows.Forms.TextBox textBoxPath;
        private System.Windows.Forms.Button buttonBrowse;

        public ModuleSelectorForm()
        {
            InitializeComponent();
            LoadLastDirectory();
            this.listBoxFolders.DoubleClick += new System.EventHandler(this.listBoxFolders_DoubleClick);
            this.StartPosition = FormStartPosition.CenterScreen;

            var version = Assembly.GetExecutingAssembly().GetName().Version;
            this.Text = $"Omnipet Module Editor v{version}";

            // Block resizing
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.SizeGripStyle = SizeGripStyle.Hide;
        }

        // =========================
        // Initialization & Settings
        // =========================

        /// <summary>
        /// Loads the last used directory from user settings.
        /// </summary>
        private void LoadLastDirectory()
        {
            string lastDir = Properties.Settings.Default.LastDirectory;
            if (string.IsNullOrEmpty(lastDir))
            {
                // Get the executable directory
                string exeDir = AppDomain.CurrentDomain.BaseDirectory;

                // Replace "\Module Editor" with "\modules"
                string modulesDir = exeDir.Replace("Module Editor", "modules");

                lastDir = modulesDir;
                Properties.Settings.Default.LastDirectory = lastDir;
                Properties.Settings.Default.Save();
            }
            if (!string.IsNullOrEmpty(lastDir) && Directory.Exists(lastDir))
            {
                textBoxPath.Text = lastDir;
                ListFoldersInDirectory(lastDir);
            }
        }

        /// <summary>
        /// Saves the last used directory to user settings.
        /// </summary>
        private void SaveLastDirectory(string path)
        {
            Properties.Settings.Default.LastDirectory = path;
            Properties.Settings.Default.Save();
        }

        // =========================
        // Directory Navigation
        // =========================

        /// <summary>
        /// Lists all folders in the specified directory in the list box.
        /// </summary>
        private void ListFoldersInDirectory(string path)
        {
            try
            {
                if (Directory.Exists(path))
                {
                    var folders = Directory.GetDirectories(path)
                        .Select(Path.GetFileName)
                        .ToArray();
                    listBoxFolders.Items.Clear();
                    listBoxFolders.Items.AddRange(folders);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    string.Format(Properties.Resources.ErrorListingFolders, ex.Message),
                    Properties.Resources.Error,
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Handles the browse button click to select a directory.
        /// </summary>
        private void buttonBrowse_Click(object sender, EventArgs e)
        {
            using (var dialog = new FolderBrowserDialog())
            {
                if (!string.IsNullOrEmpty(textBoxPath.Text) && Directory.Exists(textBoxPath.Text))
                {
                    dialog.SelectedPath = textBoxPath.Text;
                }
                if (dialog.ShowDialog() == DialogResult.OK)
                {
                    textBoxPath.Text = dialog.SelectedPath;
                    SaveLastDirectory(dialog.SelectedPath);
                    ListFoldersInDirectory(dialog.SelectedPath);
                }
            }
        }

        // =========================
        // Module Management
        // =========================

        /// <summary>
        /// Adds a new module folder and opens it in the editor.
        /// </summary>
        private void buttonAdd_Click(object sender, EventArgs e)
        {
            string input = Interaction.InputBox(
                Properties.Resources.ModuleFolderNamePrompt,
                Properties.Resources.AddModuleTitle,
                "");
            if (!string.IsNullOrWhiteSpace(input))
            {
                string currentDir = textBoxPath.Text;
                if (Directory.Exists(currentDir))
                {
                    string newFolder = Path.Combine(currentDir, input);
                    if (!Directory.Exists(newFolder))
                    {
                        Directory.CreateDirectory(newFolder);

                        // --- Load default module template from template/module.json ---
                        string templatePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "template", "module.json");
                        Models.Module newModule;
                        if (File.Exists(templatePath))
                        {
                            string json = File.ReadAllText(templatePath);
                            newModule = System.Text.Json.JsonSerializer.Deserialize<OmnipetModuleEditor.Models.Module>(json);
                        }
                        else
                        {
                            newModule = new OmnipetModuleEditor.Models.Module();
                        }
                        // Set the name to the folder name
                        newModule.Name = input;

                        // Save as module.json in the new folder
                        string moduleJsonPath = Path.Combine(newFolder, "module.json");
                        var options = new System.Text.Json.JsonSerializerOptions { WriteIndented = true };
                        File.WriteAllText(moduleJsonPath, System.Text.Json.JsonSerializer.Serialize(newModule, options));

                        ListFoldersInDirectory(currentDir);
                        var editForm = new ModuleEditorForm(newFolder, this);
                        this.Hide();
                        editForm.ShowDialog();
                    }
                    else
                    {
                        MessageBox.Show(Properties.Resources.ModuleAlreadyExists, Properties.Resources.Error, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
        }

        /// <summary>
        /// Removes the selected module folder after confirmation.
        /// </summary>
        private void buttonRemove_Click(object sender, EventArgs e)
        {
            if (listBoxFolders.SelectedItem != null)
            {
                var result = MessageBox.Show(
                    Properties.Resources.ConfirmDeleteFolder,
                    Properties.Resources.ConfirmDeletionTitle,
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Warning);

                if (result != DialogResult.Yes)
                    return;

                string currentDir = textBoxPath.Text;
                if (Directory.Exists(currentDir))
                {
                    string folderToRemove = Path.Combine(currentDir, listBoxFolders.SelectedItem.ToString());
                    try
                    {
                        Directory.Delete(folderToRemove, true);
                        ListFoldersInDirectory(currentDir);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(
                            string.Format(Properties.Resources.ErrorRemovingFolder, ex.Message),
                            Properties.Resources.Error,
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error);
                    }
                }
            }
        }

        /// <summary>
        /// Opens the selected module folder in the editor.
        /// </summary>
        private void buttonEdit_Click(object sender, EventArgs e)
        {
            if (listBoxFolders.SelectedItem != null)
            {
                string currentName = listBoxFolders.SelectedItem.ToString();
                string currentDir = textBoxPath.Text;
                if (Directory.Exists(currentDir))
                {
                    string currentPath = Path.Combine(currentDir, currentName);
                    var editForm = new ModuleEditorForm(currentPath, this);
                    this.Hide();
                    editForm.ShowDialog();
                }
            }
        }

        /// <summary>
        /// Handles double-click on a folder to open it in the editor.
        /// </summary>
        private void listBoxFolders_DoubleClick(object sender, EventArgs e)
        {
            if (listBoxFolders.SelectedItem != null)
            {
                string currentDir = textBoxPath.Text;
                string selectedFolder = listBoxFolders.SelectedItem.ToString();
                string modulePath = Path.Combine(currentDir, selectedFolder);
                if (Directory.Exists(modulePath))
                {
                    var editForm = new ModuleEditorForm(modulePath, this);
                    this.Hide();
                    editForm.ShowDialog();
                }
            }
        }
    }
}
