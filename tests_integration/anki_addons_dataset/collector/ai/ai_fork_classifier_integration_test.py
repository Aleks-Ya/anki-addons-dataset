import logging
from logging import Logger
from typing import Optional

from anki_addons_dataset.collector.ai.ai_fork_classifier import AiForkClassifier, AiForkAnswer
from anki_addons_dataset.collector.ai.ai_provider import AiProvider
from anki_addons_dataset.collector.ai.cached_ai_provider import CachedAiProvider
from anki_addons_dataset.common.data_types import AddonInfo, AddonHeader, AddonId, AddonTitle, URL, AddonRating, \
    UpdateDate, AnkiVersion, AddonPage, HtmlStr, PageLink, PageLinkSection, AddonDescription
from anki_addons_dataset.common.working_dir import SnapshotDir
from anki_addons_dataset.config.app_config import AppConfig

log: Logger = logging.getLogger(__name__)

batch_editing: AddonId = AddonId(291119185)
syntax_highlighting: AddonId = AddonId(1463041493)
mini_format_pack: AddonId = AddonId(295889520)
randomized_lists: AddonId = AddonId(1280092568)
add_note_id: AddonId = AddonId(1672832404)
progress_bar_original: AddonId = AddonId(1685464019)
progress_bar: AddonId = AddonId(2091361802)
syntax_highlighting_fork: AddonId = AddonId(1100811177)
review_heatmap: AddonId = AddonId(1771074083)
anki_connect: AddonId = AddonId(2055492159)
advanced_answer_sounds: AddonId = AddonId(1167194350)
symbols_as_you_type: AddonId = AddonId(2040501954)
fullest_screen: AddonId = AddonId(1999609504)
no_distractions: AddonId = AddonId(1049863218)
lists_to_anki: AddonId = AddonId(1029306148)
incremental_reading: AddonId = AddonId(935264945)
link_cards_notes: AddonId = AddonId(1423933177)
clickable_tags: AddonId = AddonId(1739176371)
anki_tooltips: AddonId = AddonId(1840818335)
open_in_external_editor: AddonId = AddonId(1560623518)
addon_filter_bar: AddonId = AddonId(561945101)
enhance_main_window: AddonId = AddonId(877182321)
load_balanced_scheduler: AddonId = AddonId(208879074)
book_converter: AddonId = AddonId(1837105369)
pdf_viewer: AddonId = AddonId(319501851)
anki_leaderboard: AddonId = AddonId(175794613)
code_highlighter: AddonId = AddonId(112228974)
css_injector: AddonId = AddonId(181103283)
mini_format_pack_supplementary: AddonId = AddonId(476705431)
readable_addon_folder: AddonId = AddonId(519936472)
reviewer_context_menu_search: AddonId = AddonId(359618071)
move_field_contents: AddonId = AddonId(1489826436)
free_weekend: AddonId = AddonId(742185195)
basic_to_cloze: AddonId = AddonId(800723229)
control_audio: AddonId = AddonId(1591259314)
quick_colour_changing: AddonId = AddonId(2491935955)
search_on_jisho: AddonId = AddonId(694223344)

catalog: dict[AddonId, AddonTitle] = {
    batch_editing: AddonTitle("Batch Editing"),
    syntax_highlighting: AddonTitle("Syntax Highlighting for Code"),
    mini_format_pack: AddonTitle("Mini Format Pack"),
    randomized_lists: AddonTitle("Insert Randomized Lists (multiple choice)"),
    add_note_id: AddonTitle("Add note id"),
    progress_bar_original: AddonTitle("Progress Bar (original)"),
    progress_bar: AddonTitle("Progress Bar"),
    syntax_highlighting_fork: AddonTitle("syntax highlighting FORK (css only, night-mode)"),
    review_heatmap: AddonTitle("Review Heatmap"),
    anki_connect: AddonTitle("AnkiConnect"),
    advanced_answer_sounds: AddonTitle("Advanced Answer Sounds"),
    symbols_as_you_type: AddonTitle("Symbols As You Type"),
    fullest_screen: AddonTitle("FULLEST SCREEN: hide all toolbars in reviewer"),
    no_distractions: AddonTitle("No Distractions Full Screen: Clean review interface + Tablet/Touch support"),
    lists_to_anki: AddonTitle("Lists to Anki: Convert bulletpoint lists or Org files to Anki Cards"),
    incremental_reading: AddonTitle("Incremental Reading v4.10.3"),
    link_cards_notes: AddonTitle("link Cards Notes and Preview them in extra window"),
    clickable_tags: AddonTitle("Clickable Tags v2.0"),
    anki_tooltips: AddonTitle("Anki Tooltips"),
    open_in_external_editor: AddonTitle("OpenInExternalEditor,Rename,Duplicate for Image,Audio,Video (Win,Linux)"),
    addon_filter_bar: AddonTitle("add-on dialog search/filter bar"),
    enhance_main_window: AddonTitle("Enhance main window"),
    load_balanced_scheduler: AddonTitle("Load Balanced Scheduler"),
    book_converter: AddonTitle("Converter Of Book To Hierarchical Anki Deck"),
    pdf_viewer: AddonTitle("pdf viewer and editor"),
    anki_leaderboard: AddonTitle("🏆Anki Leaderboard - Compete with friends to boost motivation (Custom by Shigeඞ)"),
    code_highlighter: AddonTitle("Greg’s Code Highlighter v1"),
    css_injector: AddonTitle("CSS Injector - Change default editor styles"),
    mini_format_pack_supplementary: AddonTitle("Mini Format Pack Supplementary"),
    readable_addon_folder: AddonTitle("Add-on folder with readable names"),
    reviewer_context_menu_search: AddonTitle("Reviewer Context Menu Search"),
    move_field_contents: AddonTitle("editor: move field contents down by one field"),
    free_weekend: AddonTitle("Free Weekend - or AOD (Legacy)"),
    basic_to_cloze: AddonTitle("Automatic Basic to Cloze (Updated)"),
    control_audio: AddonTitle("Control Audio"),
    quick_colour_changing: AddonTitle("Quick Colour Changing"),
    search_on_jisho: AddonTitle("Search on Jisho"),
}


def __classify(ai_provider: AiProvider, snapshot_dir: SnapshotDir, integration_config: AppConfig, addon_id: int,
               title: str, description: str, links: dict[AddonId, str]) -> Optional[AddonId]:
    addon_info: AddonInfo = AddonInfo(
        AddonHeader(AddonId(addon_id), AddonTitle(title), URL(f"https://ankiweb.net/shared/info/{addon_id}"),
                    AddonRating(0), UpdateDate("2026-01-01"), AnkiVersion("25.09")),
        AddonPage(HtmlStr(""), 0, 0, [], [
            PageLink(URL(f"https://ankiweb.net/shared/info/{linked_id}"), PageLinkSection.DESCRIPTION, 1, [text])
            for linked_id, text in links.items()], AddonDescription(description)),
        None, None)
    cached_ai_provider: CachedAiProvider = CachedAiProvider(ai_provider, snapshot_dir.get_ai_cache_file())
    answer: Optional[AiForkAnswer] = AiForkClassifier(
        cached_ai_provider, catalog, integration_config.ai.readme_max_chars).classify(addon_info)
    log.info(f"Answer: {answer}")
    assert answer is not None
    return answer.parent


def test_code_template_for_another_job_is_not_a_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                        integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1156270186, "Generate Batch Audio",
        "Overview An addon that generates audio in bulk from a list of URLs. Made for Anki, an SRS flashcard "
        "application. Usage Open the Anki browser and select the cards that need audio. Go to \"Edit > Generate Bulk "
        "Audio...\". Sources are listed in priority order, 1 being the first source checked/used. Credits Credit goes "
        "to the [Batch Editing addon]( https://ankiweb.net/shared/info/291119185 ) from which I used its code as a "
        "base template. This was my first Anki addon, and I would have been extremely lost if there weren't such a "
        "similar addon to mine already created and open source.",
        {batch_editing: "https://ankiweb.net/shared/info/291119185"})
    assert parent is None


def test_addon_based_on_two_addons_is_not_a_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                    integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 799647424, "Anki IPA",
        "Allows you to insert the IPA phonetic transcription of a word or a sentence into your notes by clicking on "
        "the music note button. ADDING IPA TRANSCRIPTIONS TO MULTIPLE CARDS AT ONCE It's now possible to add IPA "
        "transcriptions to multiple cards at once. Go to the Anki browser and select your Anki cards. Go to Edit/ Add "
        "IPA. CREDITS Anki IPA is based on the addons Syntax Highlighting for Code and Batch Adding by Glutanimate. "
        "Make sure to check them out!",
        {syntax_highlighting: "Syntax Highlighting for Code", batch_editing: "Batch Adding"})
    assert parent is None


def test_addon_partly_based_on_addons_is_not_a_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                       integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1261140161, "Shuffled List",
        "This add-on allows you to add unordered lists which display the list items in a random order every time you "
        "review the card. It is similar to the Insert Randomized Lists (multiple choice) but does not require a custom "
        "note type. If you have the Mini Format Pack add-on you can undo the shuffled list by highlighting the text "
        "and pressing the unordered list button. Credits This add-on is partly based on Syntax Highlighting for Code "
        "and Mini Format Pack add-ons by Glutanimate.",
        {randomized_lists: "Insert Randomized Lists (multiple choice)", mini_format_pack: "Mini Format Pack",
         syntax_highlighting: "Syntax Highlighting for Code"})
    assert parent is None


def test_code_credited_for_one_feature_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                   integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 33018515,
        "👻Anki Fade In - add fade in effect to Reviewer Home etc (Custom by Shigeඞ)",
        "Adds a fade in effect when screens change in Anki to smooth out the animation, this may help as a workaround "
        "when flickering occurs on Anki screens (e.g. Zoom add-on). This fade in feature was inspired by the add-on "
        "\" Advanced Answer Sounds \" so some of the code is credited to them. How to use Download the add-on to "
        "enable the fade in. You can change the fade in duration in the options or disable it.",
        {advanced_answer_sounds: "Advanced Answer Sounds"})
    assert parent is None


def test_config_window_code_taken_from_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                         integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 356095608,
        "editor: batch replace in one field, also with regex",
        "This add-on allows you to define a list of replacements and gives you a shortcut to apply all of these "
        "substitutions/replacements on the currently active field of the editor. Actually it's two lists: plain text "
        "and regular expressions. The code for the configuration window is taken from the great add-on Symbols As You "
        "Type by github.com/jefdongus . For batch replacements there's also the built-in find and replace "
        "functionality as well as glutanimate's Batch Editing . These do the opposite: They allow you to change one "
        "thing about multiple fields and multiple notes whereas my add-on is about changing multiple things in one "
        "field in one note.",
        {symbols_as_you_type: "Symbols As You Type", batch_editing: "Batch Editing"})
    assert parent is None


def test_bits_and_pieces_of_two_addons_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                   integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 406504899, "Hide UI",
        "Automatically hide Anki's UI while reviewing. No configuration required. Press D to return to the deck "
        "screen, E to edit a card, etc. This add-on is based on bits and pieces of Fullest Screen and No Distractions "
        ". All credit to their respective authors!",
        {fullest_screen: "Fullest Screen", no_distractions: "No Distractions"})
    assert parent is None


def test_copied_api_calls_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                      integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 443244854, "kindle2anki (light)",
        "General Purpose Generate a new deck which consists of vocabulary cards from kindle vocabulary builder ( "
        "vocab.db ). Usage Navigate: Toolbar -> Tools -> import kindle notes into Anki cards. Acknowledgement I'm new "
        "to anki add-on development. If not for previous related works, I would not be able to manage this task. I've "
        "copied and pasted codes from Lists to Anki: Convert bulletpoint lists or Org files to Anki Cards , "
        "anki-connect and wzyboy/kindle_vocab_anki . The first two helped a lot with Anki API calling. The last one "
        "helped a lot with database file conversion.",
        {lists_to_anki: "Lists to Anki: Convert bulletpoint lists or Org files to Anki Cards"})
    assert parent is None


def test_component_adjusted_from_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                   integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1095648795,
        "Cut/Copy from editor to new note or add window (with scheduling)",
        "This add-on allows to copy or cut/extract selected/highlighted content from a note in the editor to a new "
        "note. You can send the content either to a different \"Add\" window or in the background straight to the "
        "database. This allows to process a text in Anki. This add-on also has a scheduler component that was "
        "inspired by/adjusted from the Incremental Reading add-on so that cards from notes that have a special tag "
        "don't get increasing intervals when answering them.",
        {incremental_reading: "Incremental Reading"})
    assert parent is None


def test_addon_built_upon_several_addons_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                     integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1170639320, "Clickable note links",
        "This add-on allows you to create links between your cards. Paste the nid where you want the link to be, "
        "select the nid, press Cmd+Alt+L or the Ln button. Now, when you'll review the card, if you click on the nid, "
        "the browser will open on the card you linked. Alternatives & Troubleshooting If I were you, I wouldn't use "
        "this addon and instead I would opt for link Cards Notes and Preview them in extra window or one of the "
        "alternatives listed in the description of this addon. They are better maintained. My addon only supports "
        "links towards notes. Credits As mentioned in the code's commentaries, this addon is built upon link Cards "
        "Notes and Preview them in extra window , Clickable Tags v2.0 , and editor wrap selected text with custom "
        "html which has been removed from AnkiWeb since.",
        {link_cards_notes: "link Cards Notes and Preview them in extra window", clickable_tags: "Clickable Tags v2.0"})
    assert parent is None


def test_half_of_the_code_for_another_job_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                      integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1516720487, "WikiLookup",
        "Look up anything in Wikipedia from your cards, inside your cards! WikiLookup is an Anki add-on that lets you "
        "select any word/expression/sentence in your cards, hit a keyboard shortcut, and get a popup that gives you an "
        "explanation/definition of the expression with a visual. Special thanks to @kleinerpirat for the inspiration "
        "from his Anki Tooltips add-on (I stole half of its code ;P). Check his amazing add-on out!",
        {anki_tooltips: "Anki Tooltips"})
    assert parent is None


def test_borrowed_helper_code_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                          integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1584004541,
        "🖼 My Images - add images already in your anki media folder",
        "My Images is a searchable media browser and image management tool for Anki. It allows you to quickly find, "
        "preview, and insert images from your existing media collection directly into the card editor. They're only "
        "searchable if they have a decent name, so best practices is to rename your screenshots. I use this excellent "
        "addon all the time: https://ankiweb.net/shared/info/1560623518 . If you don't want to use this, I yoinked the "
        "rename code and included it in this addon, because it's useless without images with useful names.",
        {open_in_external_editor: "https://ankiweb.net/shared/info/1560623518"})
    assert parent is None


def test_feature_code_from_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                             integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1621264520, "Add-ons window  - ⬇️Sort, 🎨Colors, ✍️Hint",
        "Add-on for the Anki program. For the window with add-ons, it implements the ability to sort and color the "
        "list, it is possible to set a hint for a specific add-on. Changes for version 1.6 Added a filter field (the "
        "value is remembered and will work on the next launch) Addon-based code \"add-on dialog search/filter bar\" "
        "(user request)",
        {addon_filter_bar: "\"add-on dialog search/filter bar\""})
    assert parent is None


def test_alternative_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                       integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 12777196, "TRUE DUE: no 1000+ limit in deck overview",
        "PROBLEM: The main window caps the number of Due and New cards it shows. For example, whether you have 1,500 "
        "or 15,000 Due cards, it will only show the Due number as 1000+. SOLUTION: The true number is shown. CREDIT: "
        "The solution was derived mostly from work by Juda Kaleta . Joseph Yasmeh created this add-on to import to "
        "Anki 2.1 and to fix a major bug (explained in the code). Also added comments to explain the code. Tested on "
        "Anki 2.1.15. No plan to support versions above 2.1.27 because Anki has this feature natively in version "
        "2.1.28. This add-on is an alternative.",
        {enhance_main_window: "This add-on"})
    assert parent is None


def test_conflicting_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                       integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 742185195, "Free Weekend - or AOD (Legacy)",
        "Warning: this addon may conflict with other addons that use Anki's scheduler (load balancer, \"Load Balanced "
        "Scheduler\", and so on). If you want to use this addon integrated with Load balance, use this alternate "
        "version . Information 1: The addon does not change past schedules, only new schedules. About: Select Sunday "
        "if you do not want to study on this day or any other day of the week and this addon will select another day "
        "in the rescheduling.",
        {load_balanced_scheduler: "\"Load Balanced Scheduler\""})
    assert parent is None


def test_idea_and_code_for_one_import_mode_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                       integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1444113509, "PDF Import as a Deck to View",
        "Update 20240405: 1: Use https://ankiweb.net/shared/info/1837105369 Converter Of Book To Hierarchical Anki "
        "Deck Denis Ryazantsev's idea and codes to import pdf with heading as subdecks and add notes to every "
        "subdeck. 2: Pdf import mode add a subdeck mode: it can split a book into several sub decks. Import a pdf file "
        "as a new deck with page number cards. You can view the pdf's page through the new pdf webwiew windows. "
        "thans for these addons: https://ankiweb.net/shared/info/319501851 \"pdf viewer\"",
        {book_converter: "https://ankiweb.net/shared/info/1837105369",
         pdf_viewer: "https://ankiweb.net/shared/info/319501851"})
    assert parent is None


def test_companion_addon_is_not_fork(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                     integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 978245457,
        "📱Discord RP for Anki Leaderboard - study activity status (Created by Shigeඞ)",
        "Use RP (Rich Presence, activity status) in Discord for desktop to display your Anki leaderboard scores in "
        "Discord in real time (score display only, no direct communication with the leaderboard). The status updates "
        "every 15 seconds and the icon display changes based on reviews, time, etc. Basically this add-on is "
        "optimized for the leaderboard but you can use it even if you don't register on the leaderboard. If you are "
        "using the add-on leaderboard, the league name will be displayed.",
        {anki_leaderboard: "Anki leaderboard"})
    assert parent is None


def test_fork_is_fork_of_its_original_only(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                           integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1100811177, "syntax highlighting FORK (css only, night-mode)",
        "This add-on is not maintained In 2022 there's another syntax highlight add-on named \"Highlight Code\" that "
        "got many upvotes in a short time. Have a look at it. This add-on is a fork (modified version). For the "
        "original add-on Syntax Highlighting for Code (maintained/extened by glutanimate) click here . There are many "
        "differences between the add-ons: My version only uses css for styling, has a different gui, has an updated "
        "pygments version, etc. If you use Anki 2.1.50-2.1.54 you must also install the add-on CSS Injector . Then "
        "you must modify it by adding one line into one file of this add-on. # Credits and License see the file "
        "__init__.py of this add-on. the code to insert/wrap in \"pre\" or \"code\" tags is reused from the add-on "
        "Mini Format Pack Supplementary .",
        {code_highlighter: "syntax highlight add-on", syntax_highlighting: "here", css_injector: "CSS Injector",
         mini_format_pack_supplementary: "Mini Format Pack Supplementary"})
    assert parent == syntax_highlighting


def test_modified_version_with_a_feature_added_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                          integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 2099059923, "Batch Editing (Multi-Image Support)",
        "A modified version of the Batch Editing add-on by Glutanimate, with added support for selecting and "
        "inserting multiple media files at once. When you click the attach button, you can now hold Ctrl or Shift to "
        "select multiple images/files in one go, instead of having to click one at a time. Original add-on: Batch "
        "Editing Original author: Aristotelis P. (Glutanimate) © 2016–2023 Aristotelis P. — original code "
        "Modifications © 2024 NB",
        {batch_editing: "Batch Editing"})
    assert parent == batch_editing


def test_modified_copy_for_a_newer_anki_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                   integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 623971671, "Add Unique Identifier to all Notes",
        "Anki Add-on for Unique Note Identification This add-on is a modified (copy) of \"Add note id\" for Anki23+. "
        "Original : Add note id / Author : ospalh This Anki add-on is designed to ensure that each note has a "
        "universal unique identifier (UUID) by adding a UUID to a specified field (\"Note ID\"). It provides both a "
        "manual option to add UUIDs to all existing notes via a menu item and an automatic option that adds a UUID "
        "when a note is loaded into the editor if the field is empty.",
        {add_note_id: "Add note id"})
    assert parent == add_note_id


def test_declared_fork_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                  integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1935872040, "Accurate progress bar (mizmu addons)",
        "A fork of the Progress Bar addon { https://ankiweb.net/shared/info/1685464019 , "
        "https://ankiweb.net/shared/info/2091361802 } so that it works more accurately: The data is pulled from the "
        "database so that even if you restart Anki the data will be saved. Special treatment for filtered decks since "
        "the information about their reviews is not saved in a database. Easier configuration using the addon's "
        "config window.",
        {progress_bar_original: "https://ankiweb.net/shared/info/1685464019",
         progress_bar: "https://ankiweb.net/shared/info/2091361802"})
    assert parent == progress_bar


def test_new_fork_with_fixes_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                        integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 566351439, "Syntax Highlighting (NG)",
        "This is a new fork from the original \" Syntax Highlighting for Code \" (see References below). Allows you "
        "to insert syntax-highlighted code snippets into the spaced-repetition flashcard app Anki . The main reasons "
        "to create it is: fix these issues: PR46 PR47 clean port to python 3 adds unittests always target the latest "
        "Anki version (eg. 2.1) References Syntax Highlighting for Code release syntax highlighting FORK (css only, "
        "night-mode) release",
        {syntax_highlighting: "release", syntax_highlighting_fork: "release"})
    assert parent == syntax_highlighting


def test_extended_original_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                      integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1842249105, "Review and New added Heatmap",
        "Review and New Added Heatmap for Anki Original Add-on: Review Heatmap Original Author: Glutanimate "
        "Visualize your Anki progress like never before! This add-on provides a beautifully styled, GitHub-like "
        "heatmap right on your Anki home screen. What's different: This massive update transforms the classic Review "
        "Heatmap into a unified Dual-Mode powerhouse. Dual-Mode Toggle: A sleek, built-in dropdown menu allows you to "
        "seamlessly switch between tracking \"Reviews\" and tracking \"New Added\" cards on the fly.",
        {review_heatmap: "Review Heatmap"})
    assert parent == review_heatmap


def test_outdated_reupload_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                      integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1722241614, "RH copy 2 (outdated)",
        "IMPORTANT: This is an outdated re-upload of Review Heatmap. Please download the official version here: "
        "https://ankiweb.net/shared/info/1771074083 This listing (which was originally uploaded by a different user) "
        "is kept up for the time being to redirect and migrate people to the official upload. It will be removed in "
        "the future. – Glutanimate",
        {review_heatmap: "https://ankiweb.net/shared/info/1771074083"})
    assert parent == review_heatmap


def test_older_version_for_compatibility_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                    integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1485099361, "🔙Anki Connect Downgrader (Fork by Shigeඞ)",
        "This Add-on is for downgrading Anki Connect. You can try this if your Anki Connect is broken after updating "
        "Anki Connect. Once the original Anki Connect supports the old Anki, this Add-on is not needed. Original : "
        "Anki Connect / Author : Alex Yatskov This Add-on will overwrite the original Anki Connect, so you will "
        "receive notifications when the original is updated. How to use Install the patch for the Old Anki Connect "
        "(default: 23.10.29.0) Overwrite the original Anki Connect.(downgrade) Original Anki Connect settings will be "
        "taken over(meta.json). The purpose of this add-on is to use AnkiConnect on old Anki.",
        {anki_connect: "Anki Connect"})
    assert parent == anki_connect


def test_customized_version_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                       integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 158759867,
        "📂Readable Addons Folder - for Addons Development (Fork by Shigeඞ)",
        "This add-on is intended for developers, not general learners, and it is a customized version of \"Readable "
        "Addons Folder\" (fork). This Add-on is intended to make it easier for developers to read the Add-on folder "
        "name. This add-on creates symbolic links or junctions using the actual add-on names. Credit This add-on is "
        "not the original version, but a customized version (fork), so the important parts of the code and the ideas "
        "are credited to the author and contributors. add-on: Add-on folder with readable names / author: Arthur "
        "Milchior",
        {readable_addon_folder: "Add-on folder with readable names"})
    assert parent == readable_addon_folder


def test_patched_addon_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                  integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 2100409589, "Nederlands Leren Assistent",
        "Hoi allemaal, a'hello. A friend of mine and I worked on a quick patch up to an existing Anki add-on, the "
        "Reviewer Context Menu Search ( https://ankiweb.net/shared/info/359618071 ), which is based on Glutanimate's "
        "addon. The add on adds context menu entries for searching various online search providers.",
        {reviewer_context_menu_search: "https://ankiweb.net/shared/info/359618071"})
    assert parent == reviewer_context_menu_search


def test_portuguese_version_with_changes_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                    integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1244969965,
        "Editor: mover conteudo dos campos (move field content)",
        "Troca o conteudo do campo selecionado de cima pra baixo e de baixo pra cima Obs: so funciona se o conteudo "
        "do campo a ser trocado estiver vazio Baseado no addon editor: move field contents down by one field",
        {move_field_contents: "editor: move field contents down by one field"})
    assert parent == move_field_contents


def test_portuguese_version_with_features_added_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                           integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 925577563, "Pular fim de semana (Skip weekend)",
        "Ferramentas > Pular Baseado no addon Free Weekend - or AOD (Legacy) Versão 1.1 Seleção de multiplos decks, "
        "pesquisa de deck e manutenção do card como novo, a aprender ou a revisar apos o adiamento do deck. Versão "
        "1.0 O funcionamento é simples, primeiro seleciona um deck. Se escolher \"pular fim de semana\", todos os "
        "cards desse deck que estao programados para serem revisados no fim de semana (sabado e domingo) vao para "
        "segunda",
        {free_weekend: "Free Weekend - or AOD (Legacy)"})
    assert parent == free_weekend


def test_version_that_edits_existing_notes_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                      integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1437342223, "Automatic Basic to Cloze and Editing (Oclusao)",
        "Based on the addon Automatic Basic to Cloze (Updated) . The difference is that when the basic card already "
        "exists, it can be edited and transformed into the cloze note type. Version 2 It now works with virtually "
        "any note type you have, as long as it's not a \"Cloze\" note out of the box.",
        {basic_to_cloze: "Automatic Basic to Cloze (Updated)"})
    assert parent == basic_to_cloze


def test_version_with_more_shortcuts_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                                integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1969882468, "Control Audio Back Forward",
        "Control Audio Back Forward It is based on (Control Audio)[ https://ankiweb.net/shared/info/1591259314 ] > "
        "Press 8 to stop or continue to play the audio > Press [ to set back 5 seconds of the audio from now > Press ] "
        "to set forward 5 seconds of the audio from now",
        {control_audio: "https://ankiweb.net/shared/info/1591259314"})
    assert parent == control_audio


def test_version_that_also_bolds_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                            integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1759040096, "Bold Color Shortcut",
        "Bold Color Shortcut Change color of text and bold it quickly. Simple anki addon for adding keyboard "
        "shortcuts to quickly change the color of selected text, similar to the default Ctrl + B for bold or Ctrl + I "
        "for italic in the editor. You can toggle whether you want the text to be bolded as well by changing the "
        "config.json file. Credits: Based on Quick Colour Changing (\" https://ankiweb.net/shared/info/2491935955 \")",
        {quick_colour_changing: "https://ankiweb.net/shared/info/2491935955"})
    assert parent == quick_colour_changing


def test_generalized_version_is_fork_of(ai_provider: AiProvider, snapshot_dir: SnapshotDir,
                                        integration_config: AppConfig) -> None:
    parent: Optional[AddonId] = __classify(
        ai_provider, snapshot_dir, integration_config, 1778631913, "Quick Lookup",
        "Based on Search on Jisho (fantastic add-on, so much so that I wanted to build off it!) When you want to look "
        "up something (word, sentence, kanji, etc.), it can be a bit bothersome and time consuming to have to "
        "manually open a website in your browser and copy-paste your query every time. But no more! With this add-on "
        "you can look up words/sentences/kanji in the question field of your card with the press of a button (or by "
        "selecting text and right-clicking), as well as easily customize keyboard shortcuts and the website you "
        "search!",
        {search_on_jisho: "Search on Jisho"})
    assert parent == search_on_jisho
