using OmnimonModuleEditor.docgenerators;
using OmnimonModuleEditor.Models;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Module = OmnimonModuleEditor.Models.Module;

namespace OmnimonModuleEditor.controls
{
    internal class HTMLGenerator
    {
        public static void GenerateDocumentation(string modulePath)
        {
            try
            {
                var module = ReadModule(modulePath);
                var pets = ReadPets(modulePath);
                var enemies = ReadEnemies(modulePath);
                var items = ReadItems(modulePath);

                string docPath = Path.Combine(modulePath, "documentation");
                if (!Directory.Exists(docPath))
                    Directory.CreateDirectory(docPath);

                GeneratorUtils.CopyTemplateFiles(docPath);
                IndexGenerator.GenerateIndexPage(docPath, module);
                HomeGenerator.GenerateHomePage(docPath, module, modulePath);
                ChartGenerator.GenerateChartsPage(docPath, pets, module, modulePath);
                EnemyGenerator.GenerateEnemiesPage(docPath, enemies, module, modulePath);
                ItemGenerator.GenerateItemsPage(docPath, items);
                UnlockGenerator.GenerateUnlocksPage(docPath, module);
                BackgroundGenerator.GenerateBackgroundsPage(docPath, module); // Add this line
                QuestEventGenerator.GenerateQuestEventPage(docPath, modulePath); // Add this line
            }
            catch (Exception ex)
            {
                throw new Exception($"Error generating documentation: {ex.Message}", ex);
            }
        }





        private static string GetBackgroundUrl(int version)
        {
            return $"../images/ui/bg_ver{version}_day.png";
        }

        private static string GetStageClass(int stage)
        {
            switch (stage)
            {
                case 0: return "egg";
                case 1: return "baby";
                case 2: return "babyII";
                case 3: return "child";
                case 4: return "adult";
                case 5: return "perfect";
                case 6: return "ultimate";
                case 7: return "super";
                case 8: return "superplus";
                default: return "unknown";
            }
        }

        private static int GetLineWidth(int evolutionCount)
        {
            switch (evolutionCount)
            {
                case 1: return 30;
                case 2: return 40;
                case 3: return 50;
                default: return 30;
            }
        }

        #region Data Loading Methods

        public static Module ReadModule(string modulePath)
        {
            string moduleFile = Path.Combine(modulePath, "module.json");
            if (!File.Exists(moduleFile)) return null;
            try
            {
                string json = File.ReadAllText(moduleFile);
                return JsonSerializer.Deserialize<Module>(json);
            }
            catch
            {
                return null;
            }
        }

        public static List<Pet> ReadPets(string modulePath)
        {
            string petsFile = Path.Combine(modulePath, "monster.json");
            if (!File.Exists(petsFile)) return new List<Pet>();
            try
            {
                string json = File.ReadAllText(petsFile);
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("monster", out var petsElement))
                    {
                        return JsonSerializer.Deserialize<List<Pet>>(petsElement.GetRawText());
                    }
                }
            }
            catch { }
            return new List<Pet>();
        }

        public static List<BattleEnemy> ReadEnemies(string modulePath)
        {
            string enemiesFile = Path.Combine(modulePath, "battle.json");
            if (!File.Exists(enemiesFile)) return new List<BattleEnemy>();
            try
            {
                string json = File.ReadAllText(enemiesFile);
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("enemies", out var enemiesElement))
                    {
                        return JsonSerializer.Deserialize<List<BattleEnemy>>(enemiesElement.GetRawText());
                    }
                }
            }
            catch { }
            return new List<BattleEnemy>();
        }

        public static List<Item> ReadItems(string modulePath)
        {
            string itemsFile = Path.Combine(modulePath, "item.json");
            if (!File.Exists(itemsFile)) return new List<Item>();
            try
            {
                string json = File.ReadAllText(itemsFile);
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    var root = doc.RootElement;
                    if (root.TryGetProperty("item", out var itemsElement))
                    {
                        return JsonSerializer.Deserialize<List<Item>>(itemsElement.GetRawText());
                    }
                }
            }
            catch { }
            return new List<Item>();
        }

        #endregion
    }
}