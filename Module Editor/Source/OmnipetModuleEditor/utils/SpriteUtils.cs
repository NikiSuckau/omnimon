using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;

namespace OmnipetModuleEditor.Utils
{
    /// <summary>
    /// Sprite loading utilities for pets and enemies with fallback support and zip file compatibility.
    /// Matches the Python implementation from the game.
    /// </summary>
    public static class SpriteUtils
    {
        #region Constants

        /// <summary>
        /// Default name format used when none is specified.
        /// </summary>
        public const string DefaultNameFormat = "$_dmc";

        #endregion

        #region Public Methods

        /// <summary>
        /// Generate standardized sprite folder/zip name using module name_format.
        /// Default format is $_dmc where $ is replaced with pet name and : with _.
        /// </summary>
        /// <param name="petName">Name of the pet (e.g., "Agumon")</param>
        /// <param name="nameFormat">Format string (e.g., "$_dmc") where $ = pet name, : = _</param>
        /// <returns>Formatted sprite name (e.g., "Agumon_dmc")</returns>
        public static string GetSpriteName(string petName, string nameFormat = DefaultNameFormat)
        {
            if (string.IsNullOrEmpty(petName)) return "";
            if (string.IsNullOrEmpty(nameFormat)) nameFormat = DefaultNameFormat;

            // Replace $ with pet name and : with _
            return nameFormat.Replace("$", petName).Replace(":", "_");
        }

        /// <summary>
        /// Load pet sprites with fallback support and zip file compatibility.
        /// Matches the Python game implementation with proper fallback logic.
        /// 
        /// Loading order depends on module settings and sprite resolution preference:
        /// - If module supports hidef: Try hidef first, then regular as fallback
        /// - If module doesn't support hidef: Use regular only
        /// 
        /// For each resolution type, tries:
        /// 1. module_path/monsters(_hidef)/PetName_format/ directory
        /// 2. module_path/monsters(_hidef)/PetName_format.zip file
        /// 3. assets/monsters(_hidef)/PetName_format/ directory (fallback)
        /// 4. assets/monsters(_hidef)/PetName_format.zip file (fallback)
        /// </summary>
        /// <param name="petName">Name of the pet</param>
        /// <param name="modulePath">Path to the module folder</param>
        /// <param name="nameFormat">Format string for sprite naming (default: "$_dmc")</param>
        /// <param name="maxFrames">Maximum number of sprite frames to load</param>
        /// <param name="moduleHighDefinitionSprites">Whether module supports high definition sprites</param>
        /// <returns>Dictionary mapping sprite frame names to Images</returns>
        public static Dictionary<string, Image> LoadPetSprites(string petName, string modulePath, string nameFormat = DefaultNameFormat, int maxFrames = 20, bool moduleHighDefinitionSprites = false)
        {
            var spriteName = GetSpriteName(petName, nameFormat);
            var sprites = new Dictionary<string, Image>();

            if (string.IsNullOrEmpty(petName) || string.IsNullOrEmpty(modulePath))
                return sprites;

            // Helper function to try loading sprites from a specific folder type
            Dictionary<string, Image> TryLoadSprites(string spriteFolder, string logSuffix)
            {
                // Try module directory first
                var moduleSpritesDir = Path.Combine(modulePath, spriteFolder, spriteName);
                System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Trying {logSuffix} directory: {moduleSpritesDir}");
                var result = LoadSpritesFromDirectory(moduleSpritesDir, maxFrames);
                if (result.Count > 0)
                {
                    System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loaded {result.Count} sprites for {petName} from module {logSuffix} directory");
                    return result;
                }

                // Try module zip file
                var moduleSpriteZip = Path.Combine(modulePath, spriteFolder, $"{spriteName}.zip");
                System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Trying {logSuffix} zip: {moduleSpriteZip}");
                result = LoadSpritesFromZip(moduleSpriteZip, spriteName, maxFrames);
                if (result.Count > 0)
                {
                    System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loaded {result.Count} sprites for {petName} from module {logSuffix} zip");
                    return result;
                }

                // Try assets directory (fallback) - use the same sprite folder type
                var gameRootDirectory = Directory.GetParent(modulePath)?.Parent?.FullName;
                if (!string.IsNullOrEmpty(gameRootDirectory))
                {
                    var assetsSpritesDir = Path.Combine(gameRootDirectory, "assets", spriteFolder, spriteName);
                    System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Trying assets {logSuffix} fallback directory: {assetsSpritesDir}");
                    result = LoadSpritesFromDirectory(assetsSpritesDir, maxFrames);
                    if (result.Count > 0)
                    {
                        System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loaded {result.Count} sprites for {petName} from assets {logSuffix} fallback directory");
                        return result;
                    }

                    // Try assets zip file (fallback) - use the same sprite folder type
                    var assetsSpriteZip = Path.Combine(gameRootDirectory, "assets", spriteFolder, $"{spriteName}.zip");
                    System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Trying assets {logSuffix} fallback zip: {assetsSpriteZip}");
                    result = LoadSpritesFromZip(assetsSpriteZip, spriteName, maxFrames);
                    if (result.Count > 0)
                    {
                        System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loaded {result.Count} sprites for {petName} from assets {logSuffix} fallback zip");
                        return result;
                    }
                }

                return new Dictionary<string, Image>();
            }

            // Auto preference: Use hidef if module supports it, otherwise regular
            if (moduleHighDefinitionSprites)
            {
                // Try hidef first
                sprites = TryLoadSprites("monsters_hidef", "hidef");
                if (sprites.Count > 0)
                    return sprites;
                    
                // Fallback to regular
                System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Hidef sprites not found for {petName}, falling back to regular");
                sprites = TryLoadSprites("monsters", "regular");
                if (sprites.Count > 0)
                    return sprites;
            }
            else
            {
                // Module doesn't support hidef, use regular only
                sprites = TryLoadSprites("monsters", "regular");
                if (sprites.Count > 0)
                    return sprites;
            }

            // No sprites found
            System.Diagnostics.Debug.WriteLine($"[SpriteUtils] No sprites found for {petName} ({spriteName}) with format {nameFormat}");
            return sprites;
        }

        /// <summary>
        /// Load enemy sprites using the same fallback system as pets.
        /// </summary>
        /// <param name="enemyName">Name of the enemy</param>
        /// <param name="modulePath">Path to the module folder</param>
        /// <param name="nameFormat">Format string for sprite naming (default: "$_dmc")</param>
        /// <param name="maxFrames">Maximum number of sprite frames to load</param>
        /// <param name="moduleHighDefinitionSprites">Whether module supports high definition sprites</param>
        /// <returns>Dictionary mapping sprite frame names to Images</returns>
        public static Dictionary<string, Image> LoadEnemySprites(string enemyName, string modulePath, string nameFormat = DefaultNameFormat, int maxFrames = 20, bool moduleHighDefinitionSprites = false)
        {
            // Enemies use the same loading system as pets
            return LoadPetSprites(enemyName, modulePath, nameFormat, maxFrames, moduleHighDefinitionSprites);
        }

        /// <summary>
        /// Convert sprite dictionary to ordered list for compatibility with existing code.
        /// </summary>
        /// <param name="spritesDict">Dictionary mapping sprite names to Images</param>
        /// <param name="maxFrames">Maximum number of frames to include</param>
        /// <returns>List of sprite Images ordered by frame number (0.png, 1.png, etc.)</returns>
        public static List<Image> ConvertSpritesToList(Dictionary<string, Image> spritesDict, int maxFrames = 20)
        {
            var spriteList = new List<Image>();
            for (int i = 0; i < maxFrames; i++)
            {
                var frameName = i.ToString();
                if (spritesDict.ContainsKey(frameName))
                {
                    spriteList.Add(spritesDict[frameName]);
                }
                else
                {
                    spriteList.Add(null); // Keep the list properly indexed
                }
            }
            return spriteList;
        }

        /// <summary>
        /// Loads a single sprite (frame 0) for display purposes.
        /// </summary>
        /// <param name="petName">Name of the pet</param>
        /// <param name="modulePath">Path to the module folder</param>
        /// <param name="nameFormat">Format string for sprite naming</param>
        /// <param name="moduleHighDefinitionSprites">Whether module supports high definition sprites</param>
        /// <returns>First sprite frame or null if not found</returns>
        public static Image LoadSingleSprite(string petName, string modulePath, string nameFormat = DefaultNameFormat, bool moduleHighDefinitionSprites = false)
        {
            var sprites = LoadPetSprites(petName, modulePath, nameFormat, 1, moduleHighDefinitionSprites);
            return sprites.ContainsKey("0") ? sprites["0"] : null;
        }

        /// <summary>
        /// Loads a single enemy sprite (frame 0) for display purposes.
        /// </summary>
        /// <param name="enemyName">Name of the enemy</param>
        /// <param name="modulePath">Path to the module folder</param>
        /// <param name="nameFormat">Format string for sprite naming</param>
        /// <param name="moduleHighDefinitionSprites">Whether module supports high definition sprites</param>
        /// <returns>First sprite frame or null if not found</returns>
        public static Image LoadSingleEnemySprite(string enemyName, string modulePath, string nameFormat = DefaultNameFormat, bool moduleHighDefinitionSprites = false)
        {
            var sprites = LoadEnemySprites(enemyName, modulePath, nameFormat, 1, moduleHighDefinitionSprites);
            return sprites.ContainsKey("0") ? sprites["0"] : null;
        }

        #endregion

        #region Private Methods

        /// <summary>
        /// Load all PNG sprites from a directory.
        /// </summary>
        /// <param name="spritePath">Path to directory containing sprites</param>
        /// <param name="maxFrames">Maximum number of frames to load</param>
        /// <returns>Dictionary mapping filename (without .png) to Image</returns>
        private static Dictionary<string, Image> LoadSpritesFromDirectory(string spritePath, int maxFrames = 20)
        {
            var sprites = new Dictionary<string, Image>();
            
            if (!Directory.Exists(spritePath))
            {
                System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Directory does not exist: {spritePath}");
                return sprites;
            }

            System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loading sprites from directory: {spritePath}");

            try
            {
                var pngFiles = Directory.GetFiles(spritePath, "*.png")
                    .Where(f => 
                    {
                        var fileName = Path.GetFileNameWithoutExtension(f);
                        return int.TryParse(fileName, out var frameNum) && frameNum < maxFrames;
                    })
                    .Take(maxFrames);

                System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Found {pngFiles.Count()} PNG files matching criteria");

                foreach (var filePath in pngFiles)
                {
                    try
                    {
                        using (var fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read))
                        {
                            var img = Image.FromStream(fs);
                            var spriteName = Path.GetFileNameWithoutExtension(filePath);
                            sprites[spriteName] = new Bitmap(img);
                            System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Loaded sprite: {spriteName}");
                        }
                    }
                    catch (Exception ex)
                    {
                        // Log error but continue loading other sprites
                        System.Diagnostics.Debug.WriteLine($"Failed to load sprite {filePath}: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to read directory {spritePath}: {ex.Message}");
            }

            System.Diagnostics.Debug.WriteLine($"[SpriteUtils] Successfully loaded {sprites.Count} sprites from directory");
            return sprites;
        }

        /// <summary>
        /// Load sprites from a zip file. Supports sprites in root or in a subfolder.
        /// </summary>
        /// <param name="zipPath">Path to zip file</param>
        /// <param name="petName">Name of pet (used to check for subfolder)</param>
        /// <param name="maxFrames">Maximum number of frames to load</param>
        /// <returns>Dictionary mapping filename (without .png) to Image</returns>
        private static Dictionary<string, Image> LoadSpritesFromZip(string zipPath, string petName, int maxFrames = 20)
        {
            var sprites = new Dictionary<string, Image>();
            
            if (!File.Exists(zipPath))
                return sprites;

            try
            {
                using (var zipFile = new ZipArchive(File.OpenRead(zipPath), ZipArchiveMode.Read))
                {
                    // Get PNG files from the zip
                    var pngEntries = zipFile.Entries
                        .Where(e => e.Name.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
                        .Where(e => 
                        {
                            var fileName = Path.GetFileNameWithoutExtension(e.Name);
                            return int.TryParse(fileName, out var frameNum) && frameNum < maxFrames;
                        })
                        .Take(maxFrames);

                    foreach (var entry in pngEntries)
                    {
                        try
                        {
                            using (var entryStream = entry.Open())
                            using (var memoryStream = new MemoryStream())
                            {
                                entryStream.CopyTo(memoryStream);
                                memoryStream.Position = 0;
                                
                                var img = Image.FromStream(memoryStream);
                                var spriteName = Path.GetFileNameWithoutExtension(entry.Name);
                                sprites[spriteName] = new Bitmap(img);
                            }
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Failed to load sprite {entry.FullName} from {zipPath}: {ex.Message}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to read zip file {zipPath}: {ex.Message}");
            }

            return sprites;
        }

        #endregion
    }
}