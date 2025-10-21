using System;
using System.IO;
using System.Reflection;
using OmnimonModuleEditor.Utils;

namespace OmnimonModuleEditor.docgenerators
{
    internal class GeneratorUtils
    {
        public static string GetTemplateContent(string fileName)
        {
            var assembly = Assembly.GetExecutingAssembly();
            string templatePath = Path.Combine(Path.GetDirectoryName(assembly.Location), "template", fileName);

            System.Diagnostics.Debug.WriteLine($"GeneratorUtils: Looking for template at: {templatePath}");

            if (File.Exists(templatePath))
            {
                try
                {
                    var content = File.ReadAllText(templatePath);
                    System.Diagnostics.Debug.WriteLine($"GeneratorUtils: Successfully loaded {fileName}, size: {content.Length} characters");
                    return content;
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"GeneratorUtils: Error reading {fileName}: {ex.Message}");
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine($"GeneratorUtils: Template file {fileName} not found, using basic template");
            }

            var basicTemplate = GetBasicTemplate(fileName);
            System.Diagnostics.Debug.WriteLine($"GeneratorUtils: Using basic template for {fileName}, size: {basicTemplate.Length} characters");
            return basicTemplate;
        }

        public static string GetBasicTemplate(string fileName)
        {
            switch (fileName)
            {
                case "index.html":
                    return @"<!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <title>#MODULENAME - Module Documentation</title>
            <link rel='stylesheet' href='module.css'>
        </head>
        <body>
            <div class='module-layout'>
                <div class='module-navbar'>
                    <div class='module-logo'>#MODULENAME</div>
                    <div class='module-nav-links'>
                        <a href='home.html' target='module-content' class='active'>Module Info</a>
                        <a href='unlocks.html' target='module-content'>Unlocks</a>
                        <a href='charts.html' target='module-content'>Charts</a>
                        <a href='enemies.html' target='module-content'>Enemies</a>
                        <a href='items.html' target='module-content'>Items</a>
                        <a href='module.html' target='module-content'>Module Data</a>
                    </div>
                </div>
                <iframe name='module-content' src='home.html' class='module-frame'></iframe>
            </div>
        </body>
        </html>";

                case "home.html":
                    return @"<!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <title>#MODULENAME - Overview</title>
            <link rel='stylesheet' href='module.css'>
        </head>
        <body>
            <div class='page-content'>
                <div class='module-header'>
                    <img src='logo.png' alt='Module Logo' class='module-logo-img'>
                    <div class='module-info'>
                        <h1>#MODULENAME</h1>
                        <p class='version'>Version: #MODULEVERSION</p>
                        <p class='author'>Author: #MODULEAUTHOR</p>
                        <p class='description'>#MODULEDESCRIPTION</p>
                    </div>
                </div>
            </div>
        </body>
        </html>";

                case "charts.html":
                    return @"<!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <title>Evolution Charts</title>
            <link rel='stylesheet' href='module.css'>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }
                .page-content { max-width: 100%; margin: 0 auto; }
                .anchor { margin-bottom: 40px; }
                .family { border: 2px solid #ddd; border-radius: 10px; padding: 20px; background: #e0e0e0; }
                .digitama { display: flex; align-items: center; padding: 15px; background: rgba(255,255,255,0.9); margin-bottom: 20px; border-radius: 8px; }
                .digitama img { width: 64px; height: 64px; image-rendering: pixelated; margin-right: 15px; }
                .rdisplay { margin: 0; font-size: 18px; }
                .chart { overflow-x: auto; padding: 20px 0; position: relative; }
                .chartYellow { border-color: #f1c40f; }
                .chartBlue { border-color: #3498db; }
                .chartViolet { border-color: #9b59b6; }
                .chartRed { border-color: #e74c3c; }
                .chartGreen { border-color: #2ecc71; }
                .pet-info-row { display: flex; justify-content: space-between; margin-bottom: 8px; padding: 4px 0; border-bottom: 1px solid #eee; }
                .pet-info-label { font-weight: bold; color: #666; }
                .pet-info-value { color: #333; }
                .pet-sprite-container { text-align: center; margin-bottom: 16px; }
                .pet-sprite-img { width: 64px; height: 64px; image-rendering: pixelated; border-radius: 8px; }
                
                /* Attack sprite display */
                .attack-sprite-container {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .attack-sprite {
                    width: 24px;
                    height: 24px;
                    image-rendering: pixelated;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: #f8f9fa;
                }
                
                /* Tooltip styles */
                .tooltip {
                    position: relative;
                    cursor: help;
                    border-bottom: 1px dotted #666;
                }
                
                .tooltip .tooltiptext {
                    visibility: hidden;
                    width: 300px;
                    background-color: #333;
                    color: #fff;
                    text-align: left;
                    border-radius: 6px;
                    padding: 8px;
                    position: absolute;
                    z-index: 1001;
                    bottom: 125%;
                    left: 50%;
                    margin-left: -150px;
                    opacity: 0;
                    transition: opacity 0.3s;
                    font-size: 12px;
                    line-height: 1.4;
                    box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
                    pointer-events: none;
                }
                
                .tooltip .tooltiptext::after {
                    content: """";
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    margin-left: -5px;
                    border-width: 5px;
                    border-style: solid;
                    border-color: #333 transparent transparent transparent;
                }
                
                .tooltip:hover .tooltiptext {
                    visibility: visible;
                    opacity: 1;
                }
                
                /* Dynamic tooltip positioning classes */
                .tooltip.tooltip-left .tooltiptext {
                    left: 0;
                    margin-left: 0;
                }
                
                .tooltip.tooltip-left .tooltiptext::after {
                    left: 20px;
                    margin-left: -5px;
                }
                
                .tooltip.tooltip-right .tooltiptext {
                    right: 0;
                    left: auto;
                    margin-left: 0;
                }
                
                .tooltip.tooltip-right .tooltiptext::after {
                    right: 20px;
                    left: auto;
                    margin-left: 0;
                }
            </style>
        </head>
        <body>
            <div class='page-content'>
                <h1>Evolution Charts</h1>
                <div id='charts'>#EVOLUTIONCHARTS</div>
            </div>
            
            <!-- Evolution Choice Modal -->
            <div id='evo-modal' style='display:none; position:fixed; left:0; top:0; width:100vw; height:100vh; background:rgba(0,0,0,0.4); z-index:9999; align-items:center; justify-content:center;'>
                <div id='evo-modal-content' style='background:#fff; border-radius:8px; padding:24px; min-width:320px; max-width:90vw; max-height:80vh; overflow:auto; box-shadow:0 4px 32px #0008; position:relative;'>
                    <button onclick='closeEvoModal()' style='position:absolute; top:8px; right:12px; font-size:18px; background:none; border:none; cursor:pointer;'>&times;</button>
                    <h3>Choose One</h3>
                    <div id='evo-modal-list'></div>
                </div>
            </div>
            
            <!-- Pet Details Modal -->
            <div id='pet-modal' style='display:none; position:fixed; left:0; top:0; width:100vw; height:100vh; background:rgba(0,0,0,0.4); z-index:9999; align-items:center; justify-content:center;'>
                <div id='pet-modal-content' style='background:#fff; border-radius:8px; padding:24px; min-width:400px; max-width:90vw; max-height:80vh; overflow:auto; box-shadow:0 4px 32px #0008; position:relative;'>
                    <button onclick='closePetModal()' style='position:absolute; top:8px; right:12px; font-size:18px; background:none; border:none; cursor:pointer;'>&times;</button>
                    <div id='pet-modal-header'></div>
                    <div id='pet-modal-body'></div>
                </div>
            </div>
            
            <script>
                // Global variable to store module name format for sprite paths
                var moduleNameFormat = '$'; // Default format, will be updated when chart loads
                
                // Extract module name format from SVG metadata
                function extractModuleNameFormat() {
                    var svg = document.querySelector('svg');
                    if (svg) {
                        var metadata = svg.querySelector('moduleNameFormat');
                        if (metadata) {
                            moduleNameFormat = metadata.textContent || '$';
                            return;
                        }
                    }
                }
                
                // Get sprite URL using module name format
                function getPetSpriteUrl(petName) {
                    var safeName = petName.replace(/:/g, '_');
                    var folderName = moduleNameFormat.replace('$', safeName);
                    return '../monsters/' + folderName + '/0.png';
                }
                
                // Get attack sprite URL with fallback handling
                function loadAttackSprite(atkId, callback) {
                    if (!atkId || atkId === 0) {
                        callback(null);
                        return;
                    }
                    
                    var localPath = '../atk/' + atkId + '.png';
                    var resourcesPath = '../../resources/atk/' + atkId + '.png';
                    
                    var img = new Image();
                    img.onload = function() {
                        callback(localPath);
                    };
                    img.onerror = function() {
                        var fallbackImg = new Image();
                        fallbackImg.onload = function() {
                            callback(resourcesPath);
                        };
                        fallbackImg.onerror = function() {
                            callback(null); // No sprite found
                        };
                        fallbackImg.src = resourcesPath;
                    };
                    img.src = localPath;
                }
                
                // Function to adjust tooltip positioning based on modal boundaries
                function adjustTooltipPositions() {
                    var modal = document.getElementById('pet-modal-content');
                    if (!modal) return;
                    
                    var tooltips = modal.querySelectorAll('.tooltip');
                    var modalRect = modal.getBoundingClientRect();
                    
                    tooltips.forEach(function(tooltip) {
                        // Reset classes
                        tooltip.classList.remove('tooltip-left', 'tooltip-right');
                        
                        var tooltipRect = tooltip.getBoundingClientRect();
                        var tooltiptext = tooltip.querySelector('.tooltiptext');
                        if (!tooltiptext) return;
                        
                        // Calculate where the tooltip would appear
                        var tooltipWidth = 300; // Match CSS width
                        var tooltipLeft = tooltipRect.left + (tooltipRect.width / 2) - (tooltipWidth / 2);
                        var tooltipRight = tooltipLeft + tooltipWidth;
                        
                        // Check if tooltip would overflow modal boundaries
                        if (tooltipLeft < modalRect.left + 10) {
                            // Tooltip would overflow left, align to left edge
                            tooltip.classList.add('tooltip-left');
                        } else if (tooltipRight > modalRect.right - 10) {
                            // Tooltip would overflow right, align to right edge
                            tooltip.classList.add('tooltip-right');
                        }
                    });
                }
                
                function showPetDetails(petName, version) {
                    // Legacy function - kept for compatibility
                    alert('Pet: ' + petName + ', Version: ' + version);
                }
                
                function showPetModal(evt, el) {
                    evt.stopPropagation();
                    var data = el.getAttribute('data-pet-info');
                    var pet = {};
                    try { pet = JSON.parse(data.replace(/&quot;/g, '""')); } catch(e) { console.error('Failed to parse pet data:', e); return; }
                    
                    var header = document.getElementById('pet-modal-header');
                    var body = document.getElementById('pet-modal-body');
                    
                    // Create sprite URL using proper name format
                    var spriteUrl = getPetSpriteUrl(pet.name);
                    
                    // Header with sprite and name
                    header.innerHTML = 
                        '<div class=""pet-sprite-container"">' +
                            '<img src=""' + spriteUrl + '"" class=""pet-sprite-img"" onerror=""this.src=\'../missing.png\'"" alt=""' + pet.name + '""/>' +
                        '</div>' +
                        '<h2 style=""text-align:center; margin:0 0 16px 0; color:#333;"">' + pet.name + '</h2>';
                    
                    // Body with pet details
                    var bodyHtml = '';
                    
                    // Helper function to add info row with tooltip
                    function addRow(label, value, tooltip) {
                        if (value !== undefined && value !== null && value !== '' && value !== 0) {
                            var labelClass = tooltip ? 'pet-info-label tooltip' : 'pet-info-label';
                            var tooltipHtml = tooltip ? '<span class=""tooltiptext"">' + tooltip + '</span>' : '';
                            bodyHtml += '<div class=""pet-info-row"">' +
                                '<span class=""' + labelClass + '"">' + label + ':' + tooltipHtml + '</span>' +
                                '<span class=""pet-info-value"">' + value + '</span>' +
                                '</div>';
                        }
                    }
                    
                    // Helper function to add attack row with sprite
                    function addAttackRow(label, atkId, tooltip) {
                        if (atkId !== undefined && atkId !== null) {
                            var valueHtml = '';
                            if (atkId === 0) {
                                valueHtml = 'None';
                            } else {
                                // Create placeholder that will be updated when sprite loads
                                var containerId = 'attack-' + label.replace(/\s+/g, '') + '-' + Math.random().toString(36).substr(2, 9);
                                valueHtml = '<div class=""attack-sprite-container"" id=""' + containerId + '"">' +
                                    '<span>' + atkId + '</span>' +
                                '</div>';
                                
                                // Load sprite asynchronously
                                setTimeout(function() {
                                    loadAttackSprite(atkId, function(spriteUrl) {
                                        var container = document.getElementById(containerId);
                                        if (container && spriteUrl) {
                                            container.innerHTML = '<img src=""' + spriteUrl + '"" class=""attack-sprite"" alt=""Attack ' + atkId + '""/>' +
                                                '<span>' + atkId + '</span>';
                                        }
                                    });
                                }, 10);
                            }
                            
                            var labelClass = tooltip ? 'pet-info-label tooltip' : 'pet-info-label';
                            var tooltipHtml = tooltip ? '<span class=""tooltiptext"">' + tooltip + '</span>' : '';
                            bodyHtml += '<div class=""pet-info-row"">' +
                                '<span class=""' + labelClass + '"">' + label + ':' + tooltipHtml + '</span>' +
                                '<span class=""pet-info-value"">' + valueHtml + '</span>' +
                                '</div>';
                        }
                    }
                    
                    // Add all pet information with tooltips
                    addRow('Stage', getStageDisplayName(pet.stage), 'Evolution stage: 0=Egg, 1=Baby, 2=Baby II, 3=Child, 4=Adult, 5=Perfect, 6=Ultimate, 7=Super, 8=Super+');
                    addRow('Version', pet.version, 'Version roster this pet belongs to. Different versions may have different evolution paths and requirements.');
                    addRow('Attribute', pet.attribute || 'Free', 'Type advantage in battle: Data > Virus > Vaccine > Data. Free has no advantage/disadvantage.');
                    addRow('Special', pet.special ? 'Yes' : 'No', 'Special pets often have unique evolution requirements or unlock conditions.');
                    if (pet.special && pet.specialKey) addRow('Special Key', pet.specialKey, 'Unique identifier for special evolution or unlock conditions.');
                    addRow('Power', pet.power, 'Base battle power. Higher power increases damage output and battle effectiveness.');
                    addRow('HP', pet.hp, 'Health Points. Higher HP allows the pet to survive more damage in battles.');
                    addAttackRow('ATK Main', pet.atkMain, 'Primary attack animation ID. Used for main battle attacks and training.');
                    addAttackRow('ATK Alt', pet.atkAlt, 'Alternative attack animation ID. Used for secondary attacks or special moves.');
                    addRow('Time', pet.time + ' hours', 'Evolution timer in hours. Pet evolves when this time expires (if evolution requirements are met).');
                    addRow('Energy', pet.energy, 'Maximum DP (energy) capacity. DP is consumed during battles and training.');
                    addRow('Min Weight', pet.minWeight, 'Minimum weight threshold. Weight affects evolution paths and battle performance.');
                    if (pet.evolWeight > pet.minWeight) addRow('Evol Weight', pet.evolWeight, 'Evolution weight. Determines the starting weight of a pet after evolution.');
                    addRow('Stomach', pet.stomach, 'Hunger capacity. Determines how much food the pet can eat before becoming full.');
                    addRow('Hunger Loss', pet.hungerLoss, 'Rate of hunger depletion over time. Lower values mean hunger decreases slower.');
                    addRow('Poop Timer', pet.poopTimer + ' minutes', 'Time between pooping cycles. Neglecting poop cleanup causes care mistakes.');
                    if (pet.sleeps) addRow('Sleeps', pet.sleeps, 'Sleep start time. Pet becomes drowsy and less responsive during sleep hours.');
                    if (pet.wakes) addRow('Wakes', pet.wakes, 'Wake up time. Pet becomes active and can be interacted with normally.');
                    
                    // Add additional fields if they exist
                    if (pet.strengthLoss !== undefined) addRow('Strength Loss', pet.strengthLoss, 'Rate of strength depletion over time. Strength affects training success and evolution.');
                    if (pet.conditionHearts !== undefined) addRow('Condition Hearts', pet.conditionHearts, 'Condition/health hearts. Represents overall care quality and affects evolution.');
                    if (pet.healDoses !== undefined) addRow('Heal Doses', pet.healDoses, 'Number of medicine doses needed to cure sickness.');
                    if (pet.jogressAvailable !== undefined) addRow('Jogress Available', pet.jogressAvailable ? 'Yes' : 'No', 'Can participate in Jogress (fusion) evolution with another compatible pet.');
                    
                    body.innerHTML = bodyHtml;
                    document.getElementById('pet-modal').style.display = 'flex';
                    
                    // Adjust tooltip positions after modal is displayed and content is rendered
                    setTimeout(function() {
                        adjustTooltipPositions();
                        
                        // Add scroll listener to modal content to readjust tooltips when scrolling
                        var modalContent = document.getElementById('pet-modal-content');
                        if (modalContent) {
                            modalContent.addEventListener('scroll', function() {
                                setTimeout(adjustTooltipPositions, 10);
                            });
                        }
                    }, 50);
                }
                
                function closePetModal() {
                    document.getElementById('pet-modal').style.display = 'none';
                }
                
                function getStageDisplayName(stage) {
                    switch(stage) {
                        case 0: return 'Egg';
                        case 1: return 'Baby';
                        case 2: return 'Baby II';
                        case 3: return 'Child';
                        case 4: return 'Adult';
                        case 5: return 'Perfect';
                        case 6: return 'Ultimate';
                        case 7: return 'Super';
                        case 8: return 'Super+';
                        default: return 'Stage ' + stage;
                    }
                }
                
                function showEvoModal(evt, el) {
                    evt.stopPropagation();
                    var data = el.getAttribute('data-evos');
                    var evos = [];
                    try { evos = JSON.parse(data.replace(/&quot;/g, '""')); } catch(e) {}
                    var list = document.getElementById('evo-modal-list');
                    list.innerHTML = '';
                    if (evos.length === 0) {
                        list.innerHTML = '<div style=""color:#888;"">No criteria</div>';
                    } else {
                        evos.forEach(function(txt, i) {
                            var div = document.createElement('div');
                            div.style.marginBottom = '12px';
                            div.style.padding = '8px 12px';
                            div.style.background = '#f7f7f7';
                            div.style.borderRadius = '6px';
                            div.style.fontFamily = 'monospace';
                            div.style.fontSize = '12px';
                            div.style.lineHeight = '1.4';
                            div.innerText = 'Path ' + (i + 1) + ':\n' + txt;
                            div.style.whiteSpace = 'pre-line';
                            list.appendChild(div);
                        });
                    }
                    document.getElementById('evo-modal').style.display = 'flex';
                }
                
                function closeEvoModal() {
                    document.getElementById('evo-modal').style.display = 'none';
                }
                
                // Modal event handlers
                document.getElementById('evo-modal').onclick = closeEvoModal;
                document.getElementById('evo-modal-content').onclick = function(e){e.stopPropagation();};
                document.getElementById('pet-modal').onclick = closePetModal;
                document.getElementById('pet-modal-content').onclick = function(e){e.stopPropagation();};
                
                // Initialize module name format when page loads
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(extractModuleNameFormat, 100);
                    
                    // Add window resize listener to readjust tooltips
                    window.addEventListener('resize', function() {
                        if (document.getElementById('pet-modal').style.display === 'flex') {
                            setTimeout(adjustTooltipPositions, 100);
                        }
                    });
                });
            </script>
        </body>
        </html>";
                case "enemies.html":
                    return @"<!DOCTYPE html>
        <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <title>Battle Enemies</title>
            <link rel='stylesheet' href='module.css'>
        </head>
        <body>
            <div class='page-content'>
                <h1>Battle Enemies</h1>
                <div id='enemies-container'>#ENEMIESDATA</div>
            </div>
        </body>
        </html>";

                case "backgrounds.html":
                    return @"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Backgrounds</title>
    <link rel='stylesheet' href='module.css'>
    <style>
        .page-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        .backgrounds-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .background-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            overflow: hidden;
            border: 1px solid #e0e0e0;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .background-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        .background-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .background-name {
            font-size: 1.4em;
            font-weight: 600;
            margin: 0 0 8px 0;
        }
        .background-label {
            font-size: 1em;
            opacity: 0.9;
            margin: 0;
        }
        .background-info {
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
        }
        .background-type {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .background-type.daynight {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .background-type.static {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #74b9ff;
        }
        .sprite-section {
            margin-bottom: 20px;
        }
        .sprite-section:last-child {
            margin-bottom: 0;
        }
        .sprite-section h4 {
            margin: 0 0 12px 0;
            color: #555;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .sprite-row {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .sprite-container {
            position: relative;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            background: #f8f9fa;
            transition: border-color 0.3s ease;
        }
        .sprite-container:hover {
            border-color: #667eea;
        }
        .sprite-container.missing {
            border-color: #dc3545;
            border-style: dashed;
        }
        .sprite-image {
            display: block;
            max-width: 120px;
            max-height: 80px;
            width: auto;
            height: auto;
            image-rendering: pixelated;
        }
        .sprite-label {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 4px 8px;
            font-size: 0.75em;
            text-align: center;
        }
        .sprite-missing {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 120px;
            height: 80px;
            color: #dc3545;
            font-size: 0.8em;
            text-align: center;
            font-weight: 500;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
            font-size: 1.1em;
        }
        .empty-state i {
            font-size: 3em;
            margin-bottom: 20px;
            display: block;
            color: #ddd;
        }
    </style>
</head>
<body>
    <div class='page-content'>
        <h1>Module Backgrounds</h1>
        <div class='backgrounds-grid'>
            #BACKGROUNDSDATA
        </div>
        <div id='empty-backgrounds' class='empty-state' style='display: none;'>
            <i>🖼️</i>
            <p>No backgrounds configured for this module.</p>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var grid = document.querySelector('.backgrounds-grid');
            var emptyState = document.getElementById('empty-backgrounds');
            
            if (!grid || grid.children.length === 0) {
                grid.style.display = 'none';
                emptyState.style.display = 'block';
            }
        });
    </script>
</body>
</html>";

                case "unlocks.html":
                    return @"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Unlocks</title>
    <link rel='stylesheet' href='module.css'>
    <style>
        .unlocks-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .unlocks-table th,
        .unlocks-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }
        
        .unlocks-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            border-top: 2px solid #007bff;
        }
        
        .unlock-name {
            font-weight: 600;
            color: #007bff;
        }
        
        .unlock-label {
            font-size: 1.1em;
            color: #495057;
        }
        
        .unlock-type {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .unlock-type.egg {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffc107;
        }
        
        .unlock-type.evolution {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #74b9ff;
        }
        
        .unlock-type.adventure {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #00b894;
        }
        
        .unlock-type.digidex {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #fd79a8;
        }
        
        .unlock-type.background {
            background-color: #e2e3e5;
            color: #383d41;
            border: 1px solid #6c757d;
        }
        
        .unlock-type.group {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffc107;
        }
        
        .unlock-description {
            color: #6c757d;
            line-height: 1.4;
            font-size: 0.95em;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
            font-size: 1.1em;
        }
        
        .empty-state i {
            font-size: 3em;
            margin-bottom: 20px;
            display: block;
            color: #ddd;
        }
    </style>
</head>
<body>
    <div class='page-content'>
        <h1>Module Unlocks</h1>
        <div class='unlocks-container'>
            <table class='unlocks-table'>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Label</th>
                        <th>How to Unlock</th>
                    </tr>
                </thead>
                <tbody>
                    #UNLOCKSDATA
                </tbody>
            </table>
            <div id='empty-unlocks' class='empty-state' style='display: none;'>
                <i>🔓</i>
                <p>No unlocks configured for this module.</p>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var tbody = document.querySelector('.unlocks-table tbody');
            var emptyState = document.getElementById('empty-unlocks');
            var table = document.querySelector('.unlocks-table');
            
            if (!tbody || tbody.children.length === 0) {
                table.style.display = 'none';
                emptyState.style.display = 'block';
            }
            
            document.querySelectorAll('.unlocks-table tbody tr').forEach(function(row) {
                var typeCell = row.children[1];
                if (typeCell) {
                    var type = typeCell.textContent.trim().toLowerCase();
                    typeCell.innerHTML = '<span class=""unlock-type ' + type + '"">' + typeCell.textContent + '</span>';
                }
                
                var nameCell = row.children[0];
                if (nameCell) {
                    nameCell.classList.add('unlock-name');
                }
                
                var labelCell = row.children[2];
                if (labelCell) {
                    labelCell.classList.add('unlock-label');
                }
                
                var descCell = row.children[3];
                if (descCell) {
                    descCell.classList.add('unlock-description');
                }
            });
        });
    </script>
</body>
</html>";

                case "items.html":
                    return @"<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Items</title>
    <link rel='stylesheet' href='module.css'>
</head>
<body>
    <div class='page-content'>
        <h1>Module Items</h1>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Effect</th>
                    <th>Status</th>
                    <th>Amount</th>
                    <th>Weight Gain</th>
                </tr>
            </thead>
            <tbody>
                #ITEMSDATA
            </tbody>
        </table>
        <div id='empty-items' class='empty-state' style='display: none;'>
            <i>📦</i>
            <p>No items configured for this module.</p>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var tbody = document.querySelector('table tbody');
            var emptyState = document.getElementById('empty-items');
            var table = document.querySelector('table');
            
            if (!tbody || tbody.children.length === 0) {
                table.style.display = 'none';
                emptyState.style.display = 'block';
            }
        });
    </script>
</body>
</html>";

                default:
                    return $"<html><body><h1>{fileName} Template Not Found</h1></body></html>";
            }
        }

        public static string GetStageDisplayName(int stage)
        {
            switch (stage)
            {
                case 0: return "Egg";
                case 1: return "Baby";
                case 2: return "Baby II";
                case 3: return "Child";
                case 4: return "Adult";
                case 5: return "Perfect";
                case 6: return "Ultimate";
                case 7: return "Super";
                case 8: return "Super+";
                default: return $"Stage {stage}";
            }
        }

        public static string GetPetSprite(string petName, OmnimonModuleEditor.Models.Module module)
        {
            // Use fixed name format instead of module.NameFormat
            string spriteName = GetPetFolderName(petName, null);
            return $"../monsters/{spriteName}/0.png";
        }

        public static string GetPetFolderName(string petName, OmnimonModuleEditor.Models.Module module)
        {
            // Use fixed name format regardless of module
            return PetUtils.FixedNameFormat.Replace("$", CleanPetId(petName));
        }

        public static string CleanPetId(string petName)
        {
            return petName.Replace(" ", "_").Replace("(", "").Replace(")", "").Replace(":", "_").ToLower();
        }

        public static string GetAttributeColor(string attribute)
        {
            switch (attribute)
            {
                case "Da": return "#42a5f5";
                case "Va": return "#66bb6a";
                case "Vi": return "#ed5350";
                case "": return "#ab47bc";
                default: return "#ab47bc";
            }
        }

        public static string GetAttributeBackgroundColor(string attribute)
        {
            return GetAttributeColor(attribute);
        }

        public static void CopyTemplateFiles(string docPath)
        {
            var assembly = Assembly.GetExecutingAssembly();
            string templatePath = Path.Combine(Path.GetDirectoryName(assembly.Location), "template");

            if (Directory.Exists(templatePath))
            {
                foreach (var file in Directory.GetFiles(templatePath, "*.css"))
                {
                    File.Copy(file, Path.Combine(docPath, Path.GetFileName(file)), true);
                }
            }
        }
    }
}
