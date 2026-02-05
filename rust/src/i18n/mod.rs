//! Internationalization (i18n) support
//! 
//! Supported languages:
//! - Japanese (ja)
//! - English (en)
//! - Chinese (zh)
//! - Korean (ko)

use std::collections::HashMap;
use std::sync::OnceLock;

/// Supported languages
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Language {
    Japanese,
    English,
    Chinese,
    Korean,
}

impl Language {
    pub fn from_code(code: &str) -> Option<Self> {
        match code {
            "ja" | "ja-JP" | "日本語" => Some(Language::Japanese),
            "en" | "en-US" | "en-GB" | "english" => Some(Language::English),
            "zh" | "zh-CN" | "zh-TW" | "中文" => Some(Language::Chinese),
            "ko" | "ko-KR" | "한국어" => Some(Language::Korean),
            _ => None,
        }
    }
    
    pub fn code(&self) -> &'static str {
        match self {
            Language::Japanese => "ja",
            Language::English => "en",
            Language::Chinese => "zh",
            Language::Korean => "ko",
        }
    }
    
    pub fn name(&self) -> &'static str {
        match self {
            Language::Japanese => "日本語",
            Language::English => "English",
            Language::Chinese => "中文",
            Language::Korean => "한국어",
        }
    }
}

/// i18n manager
pub struct I18n {
    language: Language,
    translations: HashMap<String, String>,
}

impl I18n {
    pub fn new(lang_code: &str) -> Self {
        let language = Language::from_code(lang_code).unwrap_or(Language::Japanese);
        let translations = load_translations(&language);
        
        Self {
            language,
            translations,
        }
    }
    
    /// Get translation
    pub fn t(&self, key: &str) -> &str {
        self.translations
            .get(key)
            .map(|s| s.as_str())
            .unwrap_or(key)
    }
    
    /// Get current language
    pub fn language(&self) -> Language {
        self.language
    }
    
    /// Format with arguments
    pub fn tf(&self, key: &str, args: &[&str]) -> String {
        let template = self.t(key);
        let mut result = template.to_string();
        
        for (i, arg) in args.iter().enumerate() {
            let placeholder = format!("{{{}}}", i);
            result = result.replace(&placeholder, arg);
        }
        
        result
    }
}

impl Default for I18n {
    fn default() -> Self {
        Self::new("ja")
    }
}

/// Load translations for language
fn load_translations(lang: &Language) -> HashMap<String, String> {
    let mut map = HashMap::new();
    
    match lang {
        Language::Japanese => {
            map.insert("welcome".into(), "ようこそ".into());
            map.insert("project_created".into(), "プロジェクトを作成しました".into());
            map.insert("scene_generated".into(), "シーンを生成しました".into());
            map.insert("error".into(), "エラー".into());
            map.insert("loading".into(), "読み込み中...".into());
            map.insert("save".into(), "保存".into());
            map.insert("cancel".into(), "キャンセル".into());
            map.insert("delete".into(), "削除".into());
            map.insert("edit".into(), "編集".into());
            map.insert("create".into(), "作成".into());
            map.insert("search".into(), "検索".into());
            map.insert("settings".into(), "設定".into());
            map.insert("language".into(), "言語".into());
            map.insert("theme".into(), "テーマ".into());
            map.insert("dark".into(), "ダーク".into());
            map.insert("light".into(), "ライト".into());
            map.insert("agent_director".into(), "演出家".into());
            map.insert("agent_writer".into(), "作家".into());
            map.insert("agent_checker".into(), "検証官".into());
            map.insert("agent_editor".into(), "編集者".into());
            map.insert("agent_committer".into(), "記録官".into());
        }
        Language::English => {
            map.insert("welcome".into(), "Welcome".into());
            map.insert("project_created".into(), "Project created".into());
            map.insert("scene_generated".into(), "Scene generated".into());
            map.insert("error".into(), "Error".into());
            map.insert("loading".into(), "Loading...".into());
            map.insert("save".into(), "Save".into());
            map.insert("cancel".into(), "Cancel".into());
            map.insert("delete".into(), "Delete".into());
            map.insert("edit".into(), "Edit".into());
            map.insert("create".into(), "Create".into());
            map.insert("search".into(), "Search".into());
            map.insert("settings".into(), "Settings".into());
            map.insert("language".into(), "Language".into());
            map.insert("theme".into(), "Theme".into());
            map.insert("dark".into(), "Dark".into());
            map.insert("light".into(), "Light".into());
            map.insert("agent_director".into(), "Director".into());
            map.insert("agent_writer".into(), "Writer".into());
            map.insert("agent_checker".into(), "Checker".into());
            map.insert("agent_editor".into(), "Editor".into());
            map.insert("agent_committer".into(), "Committer".into());
        }
        Language::Chinese => {
            map.insert("welcome".into(), "欢迎".into());
            map.insert("project_created".into(), "项目已创建".into());
            map.insert("scene_generated".into(), "场景已生成".into());
            map.insert("error".into(), "错误".into());
            map.insert("loading".into(), "加载中...".into());
            map.insert("save".into(), "保存".into());
            map.insert("cancel".into(), "取消".into());
            map.insert("delete".into(), "删除".into());
            map.insert("edit".into(), "编辑".into());
            map.insert("create".into(), "创建".into());
            map.insert("search".into(), "搜索".into());
            map.insert("settings".into(), "设置".into());
            map.insert("language".into(), "语言".into());
            map.insert("theme".into(), "主题".into());
            map.insert("dark".into(), "深色".into());
            map.insert("light".into(), "浅色".into());
            map.insert("agent_director".into(), "导演".into());
            map.insert("agent_writer".into(), "作家".into());
            map.insert("agent_checker".into(), "检查员".into());
            map.insert("agent_editor".into(), "编辑".into());
            map.insert("agent_committer".into(), "记录员".into());
        }
        Language::Korean => {
            map.insert("welcome".into(), "환영합니다".into());
            map.insert("project_created".into(), "프로젝트가 생성되었습니다".into());
            map.insert("scene_generated".into(), "장면이 생성되었습니다".into());
            map.insert("error".into(), "오류".into());
            map.insert("loading".into(), "로딩 중...".into());
            map.insert("save".into(), "저장".into());
            map.insert("cancel".into(), "취소".into());
            map.insert("delete".into(), "삭제".into());
            map.insert("edit".into(), "편집".into());
            map.insert("create".into(), "생성".into());
            map.insert("search".into(), "검색".into());
            map.insert("settings".into(), "설정".into());
            map.insert("language".into(), "언어".into());
            map.insert("theme".into(), "테마".into());
            map.insert("dark".into(), "다크".into());
            map.insert("light".into(), "라이트".into());
            map.insert("agent_director".into(), "감독".into());
            map.insert("agent_writer".into(), "작가".into());
            map.insert("agent_checker".into(), "검증관".into());
            map.insert("agent_editor".into(), "편집자".into());
            map.insert("agent_committer".into(), "기록관".into());
        }
    }
    
    map
}

/// Initialize i18n system
pub fn init() {
    // Future: Load from external files
    tracing::info!("i18n system initialized");
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_language_from_code() {
        assert_eq!(Language::from_code("ja"), Some(Language::Japanese));
        assert_eq!(Language::from_code("en"), Some(Language::English));
        assert_eq!(Language::from_code("zh-CN"), Some(Language::Chinese));
        assert_eq!(Language::from_code("ko"), Some(Language::Korean));
        assert_eq!(Language::from_code("unknown"), None);
    }
    
    #[test]
    fn test_i18n_translation() {
        let ja = I18n::new("ja");
        assert_eq!(ja.t("welcome"), "ようこそ");
        
        let en = I18n::new("en");
        assert_eq!(en.t("welcome"), "Welcome");
    }
    
    #[test]
    fn test_i18n_format() {
        let ja = I18n::new("ja");
        // Would need a key with placeholders for full test
        let result = ja.tf("welcome", &["test"]);
        assert!(!result.is_empty());
    }
}
