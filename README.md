# EmployeeTracker Monorepo

The project now organizes the client application inside the `EmployeeTracker/client/`
folder in preparation for adding a complementary `server/` implementation.

```
EmployeeTracker/
└── client/
    ├── attendance_gui/
    ├── background_service/
    ├── commands_listener/
    ├── data_sync/
    ├── local_storage/
    ├── utils/
    ├── README.md
    └── requirements.txt
```

Each package contains placeholder modules that document the future
implementation. Imports within the client codebase have been updated to target
the new package paths so the modules continue to resolve correctly after the
move.
