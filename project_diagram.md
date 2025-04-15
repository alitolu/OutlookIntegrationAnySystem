graph TD
    subgraph UI[Views]
        MainWindow[main_window.py<br/>AWBSearchApp]
        DataSource[data_source_editor.py<br/>DataSourceEditor]
        PatternMgr[pattern_manager.py<br/>PatternManagerDialog]
        Widgets[widgets.py<br/>MailPanel]
        Progress[progress.py<br/>DetailedProgressDialog]
    end

    subgraph Core[Controllers & Models]
        SearchCtrl[search_controller.py<br/>SearchController]
        MailModel[mail_model.py<br/>MailModel]
    end

    subgraph Utils[Utilities]
        direction TB
        AWBDetector[awb_detector.py<br/>AWBDetector]
        CacheMgr[cache_manager.py<br/>CacheManager]
        ConfigMgr[config_manager.py<br/>ConfigManager]
        ExcelHelper[excel_helper.py<br/>ExcelHelper]
        MailAnalyzer[mail_analyzer.py<br/>MailAnalyzer]
        OutlookHelper[outlook_helper.py<br/>OutlookHelper]
        AIAnalyzer[ai_analyzer.py<br/>AIAnalyzer]
        AttachProc[attachment_processor.py<br/>AttachmentProcessor]
    end

    subgraph Config[Configuration]
        Settings[settings.json]
        Patterns[awb_patterns.json]
    end

    subgraph Cache[Cache & Logs]
        MailCache[mail_cache.json]
        AppLog[app.log]
    end

    %% Ana İlişkiler
    MainWindow --> SearchCtrl
    MainWindow --> MailModel
    MainWindow --> ConfigMgr
    MainWindow --> CacheMgr

    SearchCtrl --> AWBDetector
    SearchCtrl --> ExcelHelper
    SearchCtrl --> MailAnalyzer

    %% Utility İlişkileri
    AWBDetector --> Patterns
    ConfigMgr --> Settings
    CacheMgr --> MailCache
    MailAnalyzer --> AIAnalyzer
    OutlookHelper --> AttachProc

    %% UI İlişkileri
    MainWindow --> DataSource
    MainWindow --> PatternMgr
    MainWindow --> Widgets
    MainWindow --> Progress

    %% Veri Akışı
    OutlookHelper --> MailModel
    ExcelHelper --> SearchCtrl
    AIAnalyzer --> MailAnalyzer

    classDef default fill:#f9f,stroke:#333,stroke-width:2px
    classDef utils fill:#bbf,stroke:#333,stroke-width:2px
    classDef config fill:#bfb,stroke:#333,stroke-width:2px
    classDef cache fill:#fbb,stroke:#333,stroke-width:2px

    class MainWindow,DataSource,PatternMgr,Widgets,Progress default
    class AWBDetector,CacheMgr,ConfigMgr,ExcelHelper,MailAnalyzer,OutlookHelper,AIAnalyzer,AttachProc utils
    class Settings,Patterns config
    class MailCache,AppLog cache
