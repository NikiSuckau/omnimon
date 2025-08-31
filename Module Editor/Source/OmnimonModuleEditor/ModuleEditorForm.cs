using OmnimonModuleEditor.controls;
using OmnimonModuleEditor.Tabs;
using System;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace OmnimonModuleEditor
{
    /// <summary>
    /// Main form for editing a module, including tabs for module, pets, battle, and items.
    /// </summary>
    public partial class ModuleEditorForm : Form
    {
        private string currentPath;
        private Models.Module currentModule;
        private Form selectorForm;

        /// <summary>
        /// Initializes the module editor form.
        /// </summary>
        /// <param name="currentPath">Path to the module folder.</param>
        /// <param name="selectorForm">Reference to the selector form for returning after close.</param>
        public ModuleEditorForm(string currentPath, Form selectorForm)
        {
            this.currentPath = currentPath;
            this.selectorForm = selectorForm;
            InitializeComponent();

            var version = Assembly.GetExecutingAssembly().GetName().Version;
            this.Text = $"Omnimon Module Editor v{version}";

            // Block resizing
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.SizeGripStyle = SizeGripStyle.Hide;

            this.StartPosition = FormStartPosition.CenterScreen;

            LoadOrCreateModule();

            this.FormClosed += ModuleEditorForm_FormClosed;

            AddTabs();
        }

        // =========================
        // Initialization & Events
        // =========================

        /// <summary>
        /// Handles the form closed event to show the selector form again.
        /// </summary>
        private void ModuleEditorForm_FormClosed(object sender, FormClosedEventArgs e)
        {
            if (selectorForm != null)
                selectorForm.Show();
        }

        // =========================
        // Module Loading & Saving
        // =========================

        /// <summary>
        /// Loads the module from disk or creates a new one if not found.
        /// </summary>
        private void LoadOrCreateModule()
        {
            string moduleFile = Path.Combine(currentPath, "module.json");
            if (File.Exists(moduleFile))
            {
                try
                {
                    string json = File.ReadAllText(moduleFile);
                    currentModule = System.Text.Json.JsonSerializer.Deserialize<Models.Module>(json);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        string.Format(Properties.Resources.ErrorLoadingModule, ex.Message),
                        Properties.Resources.Error,
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                    currentModule = new Models.Module();
                }
            }
            else
            {
                currentModule = new Models.Module();
            }
        }

        /// <summary>
        /// Saves all tabs by calling their Save method if available.
        /// </summary>
        private void buttonSave_Click(object sender, EventArgs e)
        {
            foreach (TabPage tabPage in tabControlMain.TabPages)
            {
                if (tabPage.Controls.Count > 0)
                {
                    var control = tabPage.Controls[0];
                    var saveMethod = control.GetType().GetMethod("Save", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
                    if (saveMethod != null)
                    {
                        saveMethod.Invoke(control, null);
                    }
                }
            }
            MessageBox.Show(Properties.Resources.ModuleSaved, Properties.Resources.Save, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        /// <summary>
        /// Closes the editor form without saving.
        /// </summary>
        private void buttonCancel_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        // =========================
        // Tab Management
        // =========================

        /// <summary>
        /// Adds all main tabs (Module, Pet, Battle, Item, Quest/Event) to the tab control.
        /// </summary>
        private void AddTabs()
        {
            tabControlMain.TabPages.Clear();

            var moduleTabControl = new ModuleTab();
            moduleTabControl.Dock = DockStyle.Fill;
            moduleTabControl.SetModulePath(currentPath);
            moduleTabControl.LoadFromModule(currentModule);

            var moduleTab = new TabPage(Properties.Resources.TabModule);
            moduleTab.Controls.Add(moduleTabControl);
            tabControlMain.TabPages.Add(moduleTab);

            var petControl = new PetTab();
            petControl.Dock = DockStyle.Fill;
            petControl.SetModule(currentPath, currentModule);

            var petTab = new TabPage(Properties.Resources.TabPet);
            petTab.Controls.Add(petControl);
            tabControlMain.TabPages.Add(petTab);

            var battleTabControl = new BattleTab();
            battleTabControl.Dock = DockStyle.Fill;
            battleTabControl.SetModule(currentPath, currentModule);

            var battleTab = new TabPage(Properties.Resources.TabBattle);
            battleTab.Controls.Add(battleTabControl);
            tabControlMain.TabPages.Add(battleTab);

            var itemControl = new ItemTab();
            itemControl.Dock = DockStyle.Fill;
            itemControl.SetModule(currentPath, currentModule);

            var itemTab = new TabPage(Properties.Resources.TabItem);
            itemTab.Controls.Add(itemControl);
            tabControlMain.TabPages.Add(itemTab);

            var questEventControl = new QuestEventTab();
            questEventControl.Dock = DockStyle.Fill;
            questEventControl.SetModule(currentPath, currentModule);

            var questEventTab = new TabPage("Quests/Events");
            questEventTab.Controls.Add(questEventControl);
            tabControlMain.TabPages.Add(questEventTab);
        }

        private void buttonGenerateDoc_Click(object sender, EventArgs e)
        {
            try
            {
                HTMLGenerator.GenerateDocumentation(currentPath);
                MessageBox.Show("The module's documents were generated", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error while generating the documentation:\n" + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
