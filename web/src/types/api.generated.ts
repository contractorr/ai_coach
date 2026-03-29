// This file is generated. Do not edit manually.
// Source: web/openapi.json
// OpenAPI SHA256: fe513ae8df1cd66b9da8fe29085a47bb9bbd46354e5c85c82fe193a1358005bb
export interface paths {
    "/api/admin/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Stats */
        get: operations["get_stats_api_admin_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/ask": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Ask Advisor */
        post: operations["ask_advisor_api_advisor_ask_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/ask/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Ask Advisor Stream
         * @description SSE streaming version of /ask — emits tool_start/tool_done/answer events.
         */
        post: operations["ask_advisor_stream_api_advisor_ask_stream_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/attachments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Chat Attachment */
        post: operations["upload_chat_attachment_api_advisor_attachments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/attachments/{attachment_id}/save": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Save Chat Attachment */
        post: operations["save_chat_attachment_api_advisor_attachments__attachment_id__save_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/conversations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List User Conversations */
        get: operations["list_user_conversations_api_advisor_conversations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/conversations/{conv_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get User Conversation */
        get: operations["get_user_conversation_api_advisor_conversations__conv_id__get"];
        put?: never;
        post?: never;
        /** Delete User Conversation */
        delete: operations["delete_user_conversation_api_advisor_conversations__conv_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/traces": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Advisor Traces */
        get: operations["list_advisor_traces_api_advisor_traces_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/advisor/traces/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Advisor Trace */
        get: operations["get_advisor_trace_api_advisor_traces__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assumptions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Assumptions */
        get: operations["list_assumptions_api_assumptions_get"];
        put?: never;
        /** Create Assumption */
        post: operations["create_assumption_api_assumptions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assumptions/{assumption_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Assumption */
        patch: operations["update_assumption_api_assumptions__assumption_id__patch"];
        trace?: never;
    };
    "/api/assumptions/{assumption_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate Assumption */
        post: operations["activate_assumption_api_assumptions__assumption_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assumptions/{assumption_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive Assumption */
        post: operations["archive_assumption_api_assumptions__assumption_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/assumptions/{assumption_id}/resolve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resolve Assumption */
        post: operations["resolve_assumption_api_assumptions__assumption_id__resolve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/briefing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Briefing */
        get: operations["get_briefing_api_briefing_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/chapters/{chapter_id}/pre-reading": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Pre Reading
         * @description Get or generate pre-reading priming questions for a chapter.
         */
        get: operations["get_pre_reading_api_curriculum_chapters__chapter_id__pre_reading_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/chapters/{chapter_id}/related": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Related Chapters
         * @description Find related chapters from other enrolled guides.
         */
        get: operations["get_related_chapters_api_curriculum_chapters__chapter_id__related_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Guides */
        get: operations["list_guides_api_curriculum_guides_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/archived": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Archived Guides */
        get: operations["list_archived_guides_api_curriculum_guides_archived_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/generate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate User Guide */
        post: operations["generate_user_guide_api_curriculum_guides_generate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Guide */
        get: operations["get_guide_api_curriculum_guides__guide_id__get"];
        put?: never;
        post?: never;
        /** Archive User Guide */
        delete: operations["archive_user_guide_api_curriculum_guides__guide_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/assessments/{assessment_type}/launch": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Launch Applied Assessment */
        post: operations["launch_applied_assessment_api_curriculum_guides__guide_id__assessments__assessment_type__launch_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/assessments/{assessment_type}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Applied Assessment */
        post: operations["submit_applied_assessment_api_curriculum_guides__guide_id__assessments__assessment_type__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/chapters/{chapter_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Chapter */
        get: operations["get_chapter_api_curriculum_guides__guide_id__chapters__chapter_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/enroll": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Enroll Guide */
        post: operations["enroll_guide_api_curriculum_guides__guide_id__enroll_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/extend": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Extend Guide */
        post: operations["extend_guide_api_curriculum_guides__guide_id__extend_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/placement/generate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Generate Placement
         * @description Generate placement quiz for testing out of a guide.
         */
        post: operations["generate_placement_api_curriculum_guides__guide_id__placement_generate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/placement/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Submit Placement
         * @description Submit placement answers and grade them.
         */
        post: operations["submit_placement_api_curriculum_guides__guide_id__placement_submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/guides/{guide_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore User Guide */
        post: operations["restore_user_guide_api_curriculum_guides__guide_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/next": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Next Recommendation
         * @description Get advisor-recommended next chapter/guide to study (DAG-aware).
         */
        get: operations["get_next_recommendation_api_curriculum_next_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/progress": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Update Progress */
        post: operations["update_progress_api_curriculum_progress_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/quiz/{chapter_id}/generate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate Quiz */
        post: operations["generate_quiz_api_curriculum_quiz__chapter_id__generate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/quiz/{chapter_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit Quiz */
        post: operations["submit_quiz_api_curriculum_quiz__chapter_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Ready Guides
         * @description Return guides whose prerequisites are all completed but not yet enrolled.
         */
        get: operations["get_ready_guides_api_curriculum_ready_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/review/due": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Due Reviews */
        get: operations["get_due_reviews_api_curriculum_review_due_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/review/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Retry Reviews */
        get: operations["get_retry_reviews_api_curriculum_review_retry_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/review/{review_id}/grade": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Grade Review */
        post: operations["grade_review_api_curriculum_review__review_id__grade_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Stats */
        get: operations["get_stats_api_curriculum_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/sync": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Sync Content */
        post: operations["sync_content_api_curriculum_sync_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/teachback/{chapter_id}/generate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Generate Teachback
         * @description Generate a teach-back prompt for a completed chapter.
         */
        post: operations["generate_teachback_api_curriculum_teachback__chapter_id__generate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/teachback/{review_id}/grade": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Grade Teachback
         * @description Grade a teach-back response.
         */
        post: operations["grade_teachback_api_curriculum_teachback__review_id__grade_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/today": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Today Learning Workflow */
        get: operations["get_today_learning_workflow_api_curriculum_today_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/tracks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tracks */
        get: operations["list_tracks_api_curriculum_tracks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/curriculum/tree": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Skill Tree
         * @description Return full DAG: tracks, nodes with layout positions, edges.
         */
        get: operations["get_skill_tree_api_curriculum_tree_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dossier-escalations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Dossier Escalations */
        get: operations["list_dossier_escalations_api_dossier_escalations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dossier-escalations/{escalation_id}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Dossier Escalation */
        post: operations["accept_dossier_escalation_api_dossier_escalations__escalation_id__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dossier-escalations/{escalation_id}/dismiss": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Dismiss Dossier Escalation */
        post: operations["dismiss_dossier_escalation_api_dossier_escalations__escalation_id__dismiss_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/dossier-escalations/{escalation_id}/snooze": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Snooze Dossier Escalation */
        post: operations["snooze_dossier_escalation_api_dossier_escalations__escalation_id__snooze_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/engagement": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Post Engagement */
        post: operations["post_engagement_api_engagement_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/engagement/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Engagement Stats */
        get: operations["engagement_stats_api_engagement_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Export User Data */
        get: operations["export_user_data_api_export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/github/repos": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List User Repos
         * @description Discover user's GitHub repos.
         */
        get: operations["list_user_repos_api_github_repos_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/github/repos/monitor": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Monitor Repo
         * @description Add a repo to monitoring.
         */
        post: operations["monitor_repo_api_github_repos_monitor_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/github/repos/monitor/{repo_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Unmonitor Repo
         * @description Remove a repo from monitoring.
         */
        delete: operations["unmonitor_repo_api_github_repos_monitor__repo_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/github/repos/monitor/{repo_id}/link": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Link Goal
         * @description Link a monitored repo to a goal.
         */
        patch: operations["link_goal_api_github_repos_monitor__repo_id__link_patch"];
        trace?: never;
    };
    "/api/github/repos/monitor/{repo_id}/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Refresh Repo
         * @description Trigger immediate poll for a single repo.
         */
        post: operations["refresh_repo_api_github_repos_monitor__repo_id__refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/github/repos/monitor/{repo_id}/unlink": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Unlink Goal
         * @description Unlink a goal from a monitored repo.
         */
        patch: operations["unlink_goal_api_github_repos_monitor__repo_id__unlink_patch"];
        trace?: never;
    };
    "/api/github/repos/monitored": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Monitored
         * @description List monitored repos with latest snapshots.
         */
        get: operations["list_monitored_api_github_repos_monitored_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Goals */
        get: operations["list_goals_api_goals_get"];
        put?: never;
        /** Create Goal */
        post: operations["create_goal_api_goals_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals/{filepath}/check-in": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Check In */
        post: operations["check_in_api_goals__filepath__check_in_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals/{filepath}/milestones": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Milestone */
        post: operations["add_milestone_api_goals__filepath__milestones_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals/{filepath}/milestones/complete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Complete Milestone */
        post: operations["complete_milestone_api_goals__filepath__milestones_complete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals/{filepath}/progress": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Progress */
        get: operations["get_progress_api_goals__filepath__progress_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/goals/{filepath}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Status */
        put: operations["update_status_api_goals__filepath__status_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/greeting": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Greeting */
        get: operations["get_greeting_api_greeting_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_api_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/insights": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Insights */
        get: operations["get_insights_api_insights_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/company-movements": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Company Movements */
        get: operations["list_company_movements_api_intel_company_movements_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/company-movements/{company_key}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Company Movements */
        get: operations["get_company_movements_api_intel_company_movements__company_key__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/entities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Search Entities */
        get: operations["search_entities_api_intel_entities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/entities/{entity_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Entity */
        get: operations["get_entity_api_intel_entities__entity_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/follow-ups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Follow Ups */
        get: operations["list_follow_ups_api_intel_follow_ups_get"];
        /** Save Follow Up */
        put: operations["save_follow_up_api_intel_follow_ups_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Health
         * @description Get scraper health status for all sources.
         */
        get: operations["get_health_api_intel_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/hiring-signals": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Hiring Signals */
        get: operations["list_hiring_signals_api_intel_hiring_signals_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/hiring-signals/{entity_key}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Hiring Signals For Entity */
        get: operations["get_hiring_signals_for_entity_api_intel_hiring_signals__entity_key__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/items/{item_id}/entities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Item Entities */
        get: operations["get_item_entities_api_intel_items__item_id__entities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/preferences": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Intel Preferences
         * @description Get user's intel feed preferences.
         */
        get: operations["get_intel_preferences_api_intel_preferences_get"];
        /**
         * Update Intel Preferences
         * @description Update user's intel feed preferences.
         */
        put: operations["update_intel_preferences_api_intel_preferences_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/recent": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Recent */
        get: operations["get_recent_api_intel_recent_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/regulatory-alerts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Regulatory Alerts */
        get: operations["list_regulatory_alerts_api_intel_regulatory_alerts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/regulatory-alerts/{target_key}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Regulatory Alerts For Target */
        get: operations["get_regulatory_alerts_for_target_api_intel_regulatory_alerts__target_key__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/rss-feeds": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Rss Feeds
         * @description List user's custom RSS feeds with per-feed health.
         */
        get: operations["list_rss_feeds_api_intel_rss_feeds_get"];
        put?: never;
        /**
         * Add Rss Feed
         * @description Validate and add an RSS feed.
         */
        post: operations["add_rss_feed_api_intel_rss_feeds_post"];
        /**
         * Delete Rss Feed
         * @description Remove a user's RSS feed.
         */
        delete: operations["delete_rss_feed_api_intel_rss_feeds_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/scrape": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Scrape Now
         * @description Trigger immediate scrape of all sources.
         */
        post: operations["scrape_now_api_intel_scrape_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Search Intel */
        get: operations["search_intel_api_intel_search_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/trending": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Trending
         * @description Get cross-source trending topics, personalized by user profile.
         */
        get: operations["get_trending_api_intel_trending_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/watchlist": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Watchlist */
        get: operations["list_watchlist_api_intel_watchlist_get"];
        put?: never;
        /** Create Watchlist Item */
        post: operations["create_watchlist_item_api_intel_watchlist_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/intel/watchlist/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Watchlist Item */
        delete: operations["delete_watchlist_item_api_intel_watchlist__item_id__delete"];
        options?: never;
        head?: never;
        /** Update Watchlist Item */
        patch: operations["update_watchlist_item_api_intel_watchlist__item_id__patch"];
        trace?: never;
    };
    "/api/journal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Entries */
        get: operations["list_entries_api_journal_get"];
        put?: never;
        /** Create Entry */
        post: operations["create_entry_api_journal_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/journal/quick": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Quick Capture
         * @description Minimal journal entry — auto-title from content, type=quick, embed in ChromaDB.
         */
        post: operations["quick_capture_api_journal_quick_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/journal/{filepath}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Entry */
        get: operations["read_entry_api_journal__filepath__get"];
        /** Update Entry */
        put: operations["update_entry_api_journal__filepath__put"];
        post?: never;
        /** Delete Entry */
        delete: operations["delete_entry_api_journal__filepath__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/journal/{filepath}/mind-map": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Entry Mind Map */
        get: operations["get_entry_mind_map_api_journal__filepath__mind_map_get"];
        put?: never;
        /** Generate Entry Mind Map */
        post: operations["generate_entry_mind_map_api_journal__filepath__mind_map_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/journal/{filepath}/receipt": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Entry Receipt */
        get: operations["get_entry_receipt_api_journal__filepath__receipt_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Reports */
        get: operations["list_reports_api_library_reports_get"];
        put?: never;
        /** Create Report */
        post: operations["create_report_api_library_reports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload Report Pdf */
        post: operations["upload_report_pdf_api_library_reports_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/{report_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Report */
        get: operations["get_report_api_library_reports__report_id__get"];
        /** Update Report */
        put: operations["update_report_api_library_reports__report_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/{report_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive Report */
        post: operations["archive_report_api_library_reports__report_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/{report_id}/file": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Report File */
        get: operations["download_report_file_api_library_reports__report_id__file_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/{report_id}/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh Report */
        post: operations["refresh_report_api_library_reports__report_id__refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/library/reports/{report_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore Report */
        post: operations["restore_report_api_library_reports__report_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/memory/facts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Facts
         * @description List active facts, optionally filtered by category.
         */
        get: operations["list_facts_api_memory_facts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/memory/facts/{fact_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Fact
         * @description Get a single fact with details.
         */
        get: operations["get_fact_api_memory_facts__fact_id__get"];
        put?: never;
        post?: never;
        /**
         * Delete Fact
         * @description Soft-delete a fact.
         */
        delete: operations["delete_fact_api_memory_facts__fact_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/memory/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Stats
         * @description Get fact counts by category.
         */
        get: operations["get_stats_api_memory_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notifications */
        get: operations["list_notifications_api_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notifications/count": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Notification Count */
        get: operations["notification_count_api_notifications_count_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notifications/read-all": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark All Read */
        post: operations["mark_all_read_api_notifications_read_all_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notifications/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Read */
        post: operations["mark_read_api_notifications__notification_id__read_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/onboarding/chat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Chat Onboarding */
        post: operations["chat_onboarding_api_onboarding_chat_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/onboarding/feed-categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Feed Categories
         * @description Return all feed categories with pre-selections based on user profile.
         */
        get: operations["get_feed_categories_api_onboarding_feed_categories_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/onboarding/feeds": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Set Onboarding Feeds
         * @description Bulk-insert RSS feeds for selected categories. Idempotent via UPSERT.
         */
        post: operations["set_onboarding_feeds_api_onboarding_feeds_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/onboarding/profile-status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Profile Status
         * @description Check if user has a profile, if it's stale, and if they have an API key.
         */
        get: operations["get_profile_status_api_onboarding_profile_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/onboarding/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Onboarding */
        post: operations["start_onboarding_api_onboarding_start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/page-view": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Track Page View */
        post: operations["track_page_view_api_page_view_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Profile */
        get: operations["get_profile_api_profile_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Profile */
        patch: operations["update_profile_api_profile_patch"];
        trace?: never;
    };
    "/api/projects/ideas": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Generate Ideas
         * @description Generate project ideas via LLM.
         */
        post: operations["generate_ideas_api_projects_ideas_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/projects/issues": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Issues
         * @description Get GitHub issues matching user profile.
         */
        get: operations["get_issues_api_projects_issues_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Recommendations */
        get: operations["list_recommendations_api_recommendations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Action Items */
        get: operations["list_action_items_api_recommendations_actions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/weekly-plan": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Weekly Plan */
        get: operations["weekly_plan_api_recommendations_weekly_plan_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/{rec_id}/action-item": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Action Item */
        put: operations["update_action_item_api_recommendations__rec_id__action_item_put"];
        /** Create Action Item */
        post: operations["create_action_item_api_recommendations__rec_id__action_item_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/{rec_id}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Recommendation Feedback */
        post: operations["add_recommendation_feedback_api_recommendations__rec_id__feedback_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/{rec_id}/outcome": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Recommendation Outcome */
        get: operations["get_recommendation_outcome_api_recommendations__rec_id__outcome_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/recommendations/{rec_id}/outcome/override": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Override Recommendation Outcome */
        post: operations["override_recommendation_outcome_api_recommendations__rec_id__outcome_override_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research/dossiers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Dossiers */
        get: operations["list_dossiers_api_research_dossiers_get"];
        put?: never;
        /** Create Dossier */
        post: operations["create_dossier_api_research_dossiers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research/dossiers/{dossier_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Dossier */
        get: operations["get_dossier_api_research_dossiers__dossier_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research/dossiers/{dossier_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive Dossier */
        post: operations["archive_dossier_api_research_dossiers__dossier_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research/run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Research */
        post: operations["run_research_api_research_run_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/research/topics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Topics */
        get: operations["get_topics_api_research_topics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Settings
         * @description Return per-user settings with bool mask for secrets.
         */
        get: operations["get_settings_api_settings_get"];
        /**
         * Update Settings
         * @description Encrypt and save per-user settings.
         */
        put: operations["update_settings_api_settings_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/settings/test-custom-provider": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Test Custom Provider
         * @description Test that a custom provider configuration works.
         */
        post: operations["test_custom_provider_api_settings_test_custom_provider_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/settings/test-llm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Test Llm Connectivity
         * @description Test that the stored LLM API key works with a minimal call.
         */
        post: operations["test_llm_connectivity_api_settings_test_llm_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/settings/usage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Usage
         * @description Per-user LLM cost estimation from chat_query events.
         */
        get: operations["get_usage_api_settings_usage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/suggestions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Suggestions
         * @description Return a unified list of suggestions combining daily brief items and recommendations.
         */
        get: operations["get_suggestions_api_suggestions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Threads */
        get: operations["list_threads_api_threads_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/inbox": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Thread Inbox */
        get: operations["list_thread_inbox_api_threads_inbox_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/reindex": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reindex Threads */
        post: operations["reindex_threads_api_threads_reindex_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/{thread_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Thread */
        get: operations["get_thread_api_threads__thread_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/{thread_id}/actions/make-goal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Make Goal From Thread */
        post: operations["make_goal_from_thread_api_threads__thread_id__actions_make_goal_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/{thread_id}/actions/run-research": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run Research From Thread */
        post: operations["run_research_from_thread_api_threads__thread_id__actions_run_research_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/{thread_id}/actions/start-dossier": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Dossier From Thread */
        post: operations["start_dossier_from_thread_api_threads__thread_id__actions_start_dossier_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/threads/{thread_id}/state": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Thread State */
        patch: operations["update_thread_state_api_threads__thread_id__state_patch"];
        trace?: never;
    };
    "/api/user/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_user_me_get"];
        put?: never;
        post?: never;
        /** Delete Me */
        delete: operations["delete_me_api_user_me_delete"];
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_api_user_me_patch"];
        trace?: never;
    };
    "/metrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Metrics */
        get: operations["get_metrics_metrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AdvisorAsk */
        AdvisorAsk: {
            /**
             * Advice Type
             * @default general
             */
            advice_type: string;
            /** Attachment Ids */
            attachment_ids?: string[];
            /** Conversation Id */
            conversation_id?: string | null;
            /** Question */
            question: string;
        };
        /** AdvisorResponse */
        AdvisorResponse: {
            /** Advice Type */
            advice_type: string;
            /** Answer */
            answer: string;
            /** Conversation Id */
            conversation_id: string;
            /** Council Failed Providers */
            council_failed_providers?: string[];
            /**
             * Council Member Count
             * @default 0
             */
            council_member_count: number;
            /**
             * Council Partial
             * @default false
             */
            council_partial: boolean;
            /** Council Providers */
            council_providers?: string[];
            /**
             * Council Used
             * @default false
             */
            council_used: boolean;
            /** Degradations */
            degradations?: components["schemas"]["DegradationItem"][];
        };
        /** AssumptionAlertResponse */
        AssumptionAlertResponse: {
            /**
             * Detail
             * @default
             */
            detail: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Status
             * @default active
             */
            status: string;
            /**
             * Title
             * @default
             */
            title: string;
            /** Updated At */
            updated_at?: string | null;
        };
        /** AssumptionCreate */
        AssumptionCreate: {
            /** Extraction Confidence */
            extraction_confidence?: number | null;
            /** Linked Dossier Id */
            linked_dossier_id?: string | null;
            /**
             * Linked Entities
             * @default []
             */
            linked_entities: string[];
            /** Linked Goal Path */
            linked_goal_path?: string | null;
            /**
             * Source Id
             * @default manual
             */
            source_id: string;
            /**
             * Source Type
             * @default manual
             */
            source_type: string;
            /** Statement */
            statement: string;
            /**
             * Status
             * @default active
             */
            status: string;
        };
        /** AssumptionResponse */
        AssumptionResponse: {
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Evidence
             * @default []
             */
            evidence: {
                [key: string]: unknown;
            }[];
            /** Extraction Confidence */
            extraction_confidence?: number | null;
            /**
             * Id
             * @default
             */
            id: string;
            /** Last Evaluated At */
            last_evaluated_at?: string | null;
            /**
             * Latest Evidence Summary
             * @default
             */
            latest_evidence_summary: string;
            /** Linked Dossier Id */
            linked_dossier_id?: string | null;
            /**
             * Linked Entities
             * @default []
             */
            linked_entities: string[];
            /** Linked Goal Path */
            linked_goal_path?: string | null;
            /**
             * Source Id
             * @default
             */
            source_id: string;
            /**
             * Source Type
             * @default manual
             */
            source_type: string;
            /**
             * Statement
             * @default
             */
            statement: string;
            /**
             * Status
             * @default active
             */
            status: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
        };
        /** AssumptionUpdate */
        AssumptionUpdate: {
            /** Latest Evidence Summary */
            latest_evidence_summary?: string | null;
            /** Status */
            status?: string | null;
        };
        /** Body_upload_chat_attachment_api_advisor_attachments_post */
        Body_upload_chat_attachment_api_advisor_attachments_post: {
            /** Conversation Id */
            conversation_id?: string | null;
            /** File */
            file: string;
        };
        /** Body_upload_report_pdf_api_library_reports_upload_post */
        Body_upload_report_pdf_api_library_reports_upload_post: {
            /** Collection */
            collection?: string | null;
            /** File */
            file: string;
            /** Title */
            title?: string | null;
        };
        /** BriefingGoal */
        BriefingGoal: {
            /**
             * Days Since Check
             * @default 0
             */
            days_since_check: number;
            /**
             * Path
             * @default
             */
            path: string;
            /**
             * Status
             * @default
             */
            status: string;
            /**
             * Title
             * @default
             */
            title: string;
        };
        /** BriefingRecommendation */
        BriefingRecommendation: {
            action_item?: components["schemas"]["RecommendationActionItem"] | null;
            /**
             * Category
             * @default
             */
            category: string;
            critic?: components["schemas"]["CriticData"] | null;
            /**
             * Description
             * @default
             */
            description: string;
            /** Feedback At */
            feedback_at?: string | null;
            /** Feedback Comment */
            feedback_comment?: string | null;
            /** Harvested Outcome */
            harvested_outcome?: {
                [key: string]: unknown;
            } | null;
            /**
             * Id
             * @default
             */
            id: string;
            reasoning_trace?: components["schemas"]["ReasoningTrace"] | null;
            /**
             * Score
             * @default 0
             */
            score: number;
            /**
             * Status
             * @default
             */
            status: string;
            /**
             * Title
             * @default
             */
            title: string;
            /** User Rating */
            user_rating?: number | null;
            /**
             * Watchlist Evidence
             * @default []
             */
            watchlist_evidence: string[];
            /**
             * Why Now
             * @default []
             */
            why_now: {
                [key: string]: unknown;
            }[];
        };
        /** BriefingResponse */
        BriefingResponse: {
            /**
             * Adaptation Count
             * @default 0
             */
            adaptation_count: number;
            /**
             * Assumptions
             * @default []
             */
            assumptions: components["schemas"]["AssumptionAlertResponse"][];
            /**
             * Company Movements
             * @default []
             */
            company_movements: components["schemas"]["CompanyMovementResponse"][];
            daily_brief?: components["schemas"]["DailyBrief"] | null;
            /** Degradations */
            degradations?: components["schemas"]["DegradationItem"][];
            /**
             * Dossier Escalations
             * @default []
             */
            dossier_escalations: components["schemas"]["DossierEscalationResponse"][];
            /**
             * Goal Intel Matches
             * @default []
             */
            goal_intel_matches: components["schemas"]["GoalIntelMatch"][];
            /**
             * Goals
             * @default []
             */
            goals: components["schemas"]["BriefingGoal"][];
            /**
             * Has Data
             * @default false
             */
            has_data: boolean;
            /**
             * Hiring Signals
             * @default []
             */
            hiring_signals: components["schemas"]["HiringSignalResponse"][];
            /**
             * Recommendations
             * @default []
             */
            recommendations: components["schemas"]["BriefingRecommendation"][];
            /**
             * Regulatory Alerts
             * @default []
             */
            regulatory_alerts: components["schemas"]["RegulatoryAlertResponse"][];
            /**
             * Stale Goals
             * @default []
             */
            stale_goals: components["schemas"]["BriefingGoal"][];
        };
        /**
         * ChapterStatus
         * @enum {string}
         */
        ChapterStatus: "not_started" | "in_progress" | "completed";
        /** ChatAttachmentResponse */
        ChatAttachmentResponse: {
            /** Attachment Id */
            attachment_id: string;
            /**
             * Extracted Chars
             * @default 0
             */
            extracted_chars: number;
            /** File Name */
            file_name?: string | null;
            /**
             * Index Status
             * @default ready
             */
            index_status: string;
            /** Mime Type */
            mime_type?: string | null;
            /**
             * Visibility State
             * @default hidden
             */
            visibility_state: string;
            /** Warning */
            warning?: string | null;
        };
        /** CompanyMovementResponse */
        CompanyMovementResponse: {
            /**
             * Company Key
             * @default
             */
            company_key: string;
            /**
             * Company Label
             * @default
             */
            company_label: string;
            /**
             * Id
             * @default 0
             */
            id: number;
            /**
             * Metadata
             * @default {}
             */
            metadata: {
                [key: string]: unknown;
            };
            /**
             * Movement Type
             * @default
             */
            movement_type: string;
            /**
             * Observed At
             * @default
             */
            observed_at: string;
            /**
             * Significance
             * @default 0
             */
            significance: number;
            /**
             * Source Family
             * @default
             */
            source_family: string;
            /**
             * Source Url
             * @default
             */
            source_url: string;
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Title
             * @default
             */
            title: string;
        };
        /** ConversationAttachment */
        ConversationAttachment: {
            /** File Name */
            file_name?: string | null;
            /** Library Item Id */
            library_item_id: string;
            /** Mime Type */
            mime_type?: string | null;
        };
        /** ConversationDetail */
        ConversationDetail: {
            /** Id */
            id: string;
            /** Messages */
            messages: components["schemas"]["ConversationMessage"][];
            /** Title */
            title: string;
        };
        /** ConversationListItem */
        ConversationListItem: {
            /** Id */
            id: string;
            /** Message Count */
            message_count: number;
            /** Title */
            title: string;
            /** Updated At */
            updated_at: string;
        };
        /** ConversationMessage */
        ConversationMessage: {
            /** Attachments */
            attachments?: components["schemas"]["ConversationAttachment"][];
            /** Content */
            content: string;
            /** Created At */
            created_at: string;
            /** Id */
            id?: string | null;
            /** Role */
            role: string;
        };
        /**
         * CriticData
         * @description Adversarial critic output for a recommendation.
         */
        CriticData: {
            /** Alternative */
            alternative?: string | null;
            /**
             * Confidence
             * @default Medium
             */
            confidence: string;
            /**
             * Confidence Rationale
             * @default
             */
            confidence_rationale: string;
            /**
             * Critic Challenge
             * @default
             */
            critic_challenge: string;
            /** Intel Contradictions */
            intel_contradictions?: string | null;
            /**
             * Missing Context
             * @default
             */
            missing_context: string;
        };
        /** CustomProviderCreate */
        CustomProviderCreate: {
            /** Api Key */
            api_key: string;
            /** Base Url */
            base_url: string;
            /** Display Name */
            display_name: string;
            /** Model */
            model: string;
        };
        /** CustomProviderInfo */
        CustomProviderInfo: {
            /** Base Url */
            base_url: string;
            /** Display Name */
            display_name: string;
            /** Id */
            id: string;
            /** Model */
            model: string;
        };
        /** CustomProviderUpdate */
        CustomProviderUpdate: {
            /** Api Key */
            api_key?: string | null;
            /** Base Url */
            base_url?: string | null;
            /** Display Name */
            display_name?: string | null;
            /** Id */
            id: string;
            /** Model */
            model?: string | null;
        };
        /** DailyBrief */
        DailyBrief: {
            /**
             * Budget Minutes
             * @default 0
             */
            budget_minutes: number;
            /**
             * Generated At
             * @default
             */
            generated_at: string;
            /**
             * Items
             * @default []
             */
            items: components["schemas"]["DailyBriefItem"][];
            /**
             * Used Minutes
             * @default 0
             */
            used_minutes: number;
        };
        /** DailyBriefItem */
        DailyBriefItem: {
            /**
             * Action
             * @default
             */
            action: string;
            /**
             * Description
             * @default
             */
            description: string;
            /**
             * Kind
             * @default
             */
            kind: string;
            /**
             * Priority
             * @default 0
             */
            priority: number;
            /**
             * Time Minutes
             * @default 0
             */
            time_minutes: number;
            /**
             * Title
             * @default
             */
            title: string;
        };
        /** DegradationItem */
        DegradationItem: {
            /** Component */
            component: string;
            /** Message */
            message: string;
        };
        /** DossierCreateRequest */
        DossierCreateRequest: {
            /** Assumptions */
            assumptions?: string[];
            /** Core Questions */
            core_questions?: string[];
            /** Open Questions */
            open_questions?: string[];
            /** Related Goals */
            related_goals?: string[];
            /**
             * Scope
             * @default
             */
            scope: string;
            /** Topic */
            topic: string;
            /** Tracked Subtopics */
            tracked_subtopics?: string[];
        };
        /** DossierEscalationResponse */
        DossierEscalationResponse: {
            /** Accepted Dossier Id */
            accepted_dossier_id?: string | null;
            /**
             * Created At
             * @default
             */
            created_at: string;
            /** Dismissed At */
            dismissed_at?: string | null;
            /**
             * Escalation Id
             * @default
             */
            escalation_id: string;
            /**
             * Evidence
             * @default {}
             */
            evidence: {
                [key: string]: unknown;
            };
            /**
             * Payload
             * @default {}
             */
            payload: {
                [key: string]: unknown;
            };
            /**
             * Score
             * @default 0
             */
            score: number;
            /** Snoozed Until */
            snoozed_until?: string | null;
            /**
             * State
             * @default active
             */
            state: string;
            /**
             * Topic Key
             * @default
             */
            topic_key: string;
            /**
             * Topic Label
             * @default
             */
            topic_label: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
        };
        /** DossierEscalationSnoozeRequest */
        DossierEscalationSnoozeRequest: {
            /** Until */
            until?: string | null;
        };
        /** EngagementEvent */
        EngagementEvent: {
            /** Event Type */
            event_type: string;
            /** Metadata */
            metadata?: {
                [key: string]: unknown;
            } | null;
            /** Target Id */
            target_id: string;
            /** Target Type */
            target_type: string;
        };
        /** EngagementStats */
        EngagementStats: {
            /**
             * By Event
             * @default {}
             */
            by_event: {
                [key: string]: unknown;
            };
            /**
             * By Target
             * @default {}
             */
            by_target: {
                [key: string]: unknown;
            };
            /**
             * Total
             * @default 0
             */
            total: number;
        };
        /** ExtractionReceiptEnvelope */
        ExtractionReceiptEnvelope: {
            /** Receipt */
            receipt?: {
                [key: string]: unknown;
            } | null;
            /**
             * Status
             * @default pending
             */
            status: string;
        };
        /** FeedCategoryItem */
        FeedCategoryItem: {
            /** Feed Count */
            feed_count: number;
            /** Icon */
            icon: string;
            /** Id */
            id: string;
            /** Label */
            label: string;
            /**
             * Preselected
             * @default false
             */
            preselected: boolean;
        };
        /** FollowUpUpsert */
        FollowUpUpsert: {
            /**
             * Note
             * @default
             */
            note: string;
            /**
             * Saved
             * @default false
             */
            saved: boolean;
            /** Title */
            title: string;
            /** Url */
            url: string;
            /**
             * Watchlist Ids
             * @default []
             */
            watchlist_ids: string[];
        };
        /** GoalCheckIn */
        GoalCheckIn: {
            /** Notes */
            notes?: string | null;
        };
        /** GoalCreate */
        GoalCreate: {
            /**
             * Content
             * @default
             */
            content: string;
            /** Tags */
            tags?: string[] | null;
            /** Title */
            title: string;
        };
        /** GoalIntelMatch */
        GoalIntelMatch: {
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Goal Path
             * @default
             */
            goal_path: string;
            /**
             * Goal Title
             * @default
             */
            goal_title: string;
            /**
             * Id
             * @default 0
             */
            id: number;
            /**
             * Llm Evaluated
             * @default false
             */
            llm_evaluated: boolean;
            /**
             * Match Reasons
             * @default []
             */
            match_reasons: string[];
            /**
             * Score
             * @default 0
             */
            score: number;
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Urgency
             * @default
             */
            urgency: string;
            /**
             * Url
             * @default
             */
            url: string;
        };
        /** GoalStatusUpdate */
        GoalStatusUpdate: {
            /** Status */
            status: string;
        };
        /** GreetingResponse */
        GreetingResponse: {
            /**
             * Cached
             * @default false
             */
            cached: boolean;
            /** Degradations */
            degradations?: components["schemas"]["DegradationItem"][];
            /** Return Brief */
            return_brief?: {
                [key: string]: unknown;
            } | null;
            /**
             * Stale
             * @default false
             */
            stale: boolean;
            /** Text */
            text: string;
        };
        /**
         * GuideDepth
         * @enum {string}
         */
        GuideDepth: "survey" | "practitioner" | "deep_dive";
        /** GuideExtensionRequest */
        GuideExtensionRequest: {
            /** Audience */
            audience?: string | null;
            depth?: components["schemas"]["GuideDepth"] | null;
            /** Instruction */
            instruction?: string | null;
            /** Prompt */
            prompt: string;
            /** Time Budget */
            time_budget?: string | null;
        };
        /** GuideGenerationRequest */
        GuideGenerationRequest: {
            /** Audience */
            audience: string;
            depth: components["schemas"]["GuideDepth"];
            /** Instruction */
            instruction?: string | null;
            /** Time Budget */
            time_budget: string;
            /** Topic */
            topic: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HiringSignalResponse */
        HiringSignalResponse: {
            /**
             * Entity Key
             * @default
             */
            entity_key: string;
            /**
             * Entity Label
             * @default
             */
            entity_label: string;
            /**
             * Id
             * @default 0
             */
            id: number;
            /**
             * Metadata
             * @default {}
             */
            metadata: {
                [key: string]: unknown;
            };
            /**
             * Observed At
             * @default
             */
            observed_at: string;
            /**
             * Signal Type
             * @default
             */
            signal_type: string;
            /**
             * Source Url
             * @default
             */
            source_url: string;
            /**
             * Strength
             * @default 0
             */
            strength: number;
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Title
             * @default
             */
            title: string;
        };
        /** InsightResponse */
        InsightResponse: {
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Detail
             * @default
             */
            detail: string;
            /**
             * Evidence
             * @default []
             */
            evidence: string[];
            /** Expires At */
            expires_at?: string | null;
            /**
             * Id
             * @default 0
             */
            id: number;
            /**
             * Insight Hash
             * @default
             */
            insight_hash: string;
            /**
             * Severity
             * @default 0
             */
            severity: number;
            /**
             * Source Url
             * @default
             */
            source_url: string;
            /**
             * Suggested Actions
             * @default []
             */
            suggested_actions: string[];
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Type
             * @default
             */
            type: string;
            /**
             * Watchlist Evidence
             * @default []
             */
            watchlist_evidence: string[];
        };
        /** IntelFollowUp */
        IntelFollowUp: {
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Note
             * @default
             */
            note: string;
            /**
             * Saved
             * @default false
             */
            saved: boolean;
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
            /**
             * Url
             * @default
             */
            url: string;
            /**
             * Watchlist Ids
             * @default []
             */
            watchlist_ids: string[];
        };
        /** IntelPreferencesUpdate */
        IntelPreferencesUpdate: {
            /** Excluded Keywords */
            excluded_keywords?: string[] | null;
            /** Excluded Sources */
            excluded_sources?: string[] | null;
            /** Min Relevance */
            min_relevance?: number | null;
            /** Preferred Sources */
            preferred_sources?: string[] | null;
        };
        /** JournalCreate */
        JournalCreate: {
            /** Content */
            content: string;
            /**
             * Entry Type
             * @default daily
             */
            entry_type: string;
            /** Tags */
            tags?: string[] | null;
            /** Title */
            title?: string | null;
        };
        /** JournalEntry */
        JournalEntry: {
            /** Content */
            content?: string | null;
            /** Created */
            created?: string | null;
            /**
             * Metadata
             * @default {}
             */
            metadata: {
                [key: string]: unknown;
            };
            /** Path */
            path: string;
            /**
             * Preview
             * @default
             */
            preview: string;
            /**
             * Tags
             * @default []
             */
            tags: string[];
            /** Title */
            title: string;
            /** Type */
            type: string;
        };
        /** JournalMindMapEdge */
        JournalMindMapEdge: {
            /**
             * Label
             * @default
             */
            label: string;
            /** Source */
            source: string;
            /**
             * Strength
             * @default 0
             */
            strength: number;
            /** Target */
            target: string;
        };
        /** JournalMindMapEnvelope */
        JournalMindMapEnvelope: {
            mind_map?: components["schemas"]["JournalMindMapResponse"] | null;
            /**
             * Status
             * @default not_available
             * @enum {string}
             */
            status: "ready" | "not_available" | "insufficient_signal";
        };
        /** JournalMindMapNode */
        JournalMindMapNode: {
            /**
             * Confidence
             * @default 0
             */
            confidence: number;
            /** Id */
            id: string;
            /**
             * Is Root
             * @default false
             */
            is_root: boolean;
            /** Kind */
            kind: string;
            /** Label */
            label: string;
            /**
             * Source Label
             * @default
             */
            source_label: string;
            /**
             * Source Ref
             * @default
             */
            source_ref: string;
            /** Source Type */
            source_type?: string | null;
            /**
             * Weight
             * @default 0
             */
            weight: number;
        };
        /** JournalMindMapResponse */
        JournalMindMapResponse: {
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Edges
             * @default []
             */
            edges: components["schemas"]["JournalMindMapEdge"][];
            /** Entry Path */
            entry_path: string;
            /** Entry Title */
            entry_title: string;
            /**
             * Generator
             * @default
             */
            generator: string;
            /** Map Id */
            map_id: string;
            /**
             * Nodes
             * @default []
             */
            nodes: components["schemas"]["JournalMindMapNode"][];
            /**
             * Rationale
             * @default
             */
            rationale: string;
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
        };
        /** JournalUpdate */
        JournalUpdate: {
            /** Content */
            content?: string | null;
            /** Metadata */
            metadata?: {
                [key: string]: unknown;
            } | null;
        };
        /** LLMProviderKeyStatus */
        LLMProviderKeyStatus: {
            /**
             * Configured
             * @default false
             */
            configured: boolean;
            /**
             * Council Eligible
             * @default false
             */
            council_eligible: boolean;
            /** Hint */
            hint?: string | null;
            /** Provider */
            provider: string;
        };
        /** LibraryReportCreate */
        LibraryReportCreate: {
            /** Collection */
            collection?: string | null;
            /** Prompt */
            prompt: string;
            /**
             * Report Type
             * @default custom
             */
            report_type: string;
            /** Title */
            title?: string | null;
        };
        /** LibraryReportListItem */
        LibraryReportListItem: {
            /** Collection */
            collection?: string | null;
            /**
             * Created
             * @default
             */
            created: string;
            /**
             * Extracted Chars
             * @default 0
             */
            extracted_chars: number;
            /** Extraction Status */
            extraction_status?: string | null;
            /** File Name */
            file_name?: string | null;
            /** File Size */
            file_size?: number | null;
            /**
             * Has Attachment
             * @default false
             */
            has_attachment: boolean;
            /**
             * Has Extracted Text
             * @default false
             */
            has_extracted_text: boolean;
            /** Id */
            id: string;
            /** Index Status */
            index_status?: string | null;
            /**
             * Last Generated At
             * @default
             */
            last_generated_at: string;
            /** Mime Type */
            mime_type?: string | null;
            /**
             * Origin Surface
             * @default library
             */
            origin_surface: string;
            /**
             * Preview
             * @default
             */
            preview: string;
            /**
             * Prompt
             * @default
             */
            prompt: string;
            /** Report Type */
            report_type: string;
            /**
             * Source Kind
             * @default generated
             */
            source_kind: string;
            /** Status */
            status: string;
            /** Title */
            title: string;
            /**
             * Updated
             * @default
             */
            updated: string;
            /**
             * Visibility State
             * @default saved
             */
            visibility_state: string;
        };
        /** LibraryReportResponse */
        LibraryReportResponse: {
            /** Collection */
            collection?: string | null;
            /**
             * Content
             * @default
             */
            content: string;
            /**
             * Created
             * @default
             */
            created: string;
            /**
             * Extracted Chars
             * @default 0
             */
            extracted_chars: number;
            /** Extraction Status */
            extraction_status?: string | null;
            /** File Name */
            file_name?: string | null;
            /** File Size */
            file_size?: number | null;
            /**
             * Has Attachment
             * @default false
             */
            has_attachment: boolean;
            /**
             * Has Extracted Text
             * @default false
             */
            has_extracted_text: boolean;
            /** Id */
            id: string;
            /** Index Status */
            index_status?: string | null;
            /**
             * Last Generated At
             * @default
             */
            last_generated_at: string;
            /** Mime Type */
            mime_type?: string | null;
            /**
             * Origin Surface
             * @default library
             */
            origin_surface: string;
            /**
             * Preview
             * @default
             */
            preview: string;
            /**
             * Prompt
             * @default
             */
            prompt: string;
            /** Report Type */
            report_type: string;
            /**
             * Source Kind
             * @default generated
             */
            source_kind: string;
            /** Status */
            status: string;
            /** Title */
            title: string;
            /**
             * Updated
             * @default
             */
            updated: string;
            /**
             * Visibility State
             * @default saved
             */
            visibility_state: string;
        };
        /** LibraryReportUpdate */
        LibraryReportUpdate: {
            /** Collection */
            collection?: string | null;
            /** Content */
            content?: string | null;
            /** Title */
            title?: string | null;
        };
        /** LinkGoalRequest */
        LinkGoalRequest: {
            /** Goal Path */
            goal_path: string;
        };
        /** MemoryFact */
        MemoryFact: {
            /**
             * Category
             * @default
             */
            category: string;
            /**
             * Confidence
             * @default 0
             */
            confidence: number;
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Source Id
             * @default
             */
            source_id: string;
            /**
             * Source Type
             * @default
             */
            source_type: string;
            /**
             * Text
             * @default
             */
            text: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
        };
        /** MemoryStats */
        MemoryStats: {
            /**
             * By Category
             * @default {}
             */
            by_category: {
                [key: string]: unknown;
            };
            /**
             * Total Active
             * @default 0
             */
            total_active: number;
            /**
             * Total Superseded
             * @default 0
             */
            total_superseded: number;
        };
        /** MilestoneAdd */
        MilestoneAdd: {
            /** Title */
            title: string;
        };
        /** MilestoneComplete */
        MilestoneComplete: {
            /** Milestone Index */
            milestone_index: number;
        };
        /** MonitorRepoRequest */
        MonitorRepoRequest: {
            /**
             * Html Url
             * @default
             */
            html_url: string;
            /**
             * Is Private
             * @default false
             */
            is_private: boolean;
            /** Repo Full Name */
            repo_full_name: string;
        };
        /** MonitoredRepoResponse */
        MonitoredRepoResponse: {
            /**
             * Added At
             * @default
             */
            added_at: string;
            /**
             * Html Url
             * @default
             */
            html_url: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Is Private
             * @default false
             */
            is_private: boolean;
            /** Last Polled At */
            last_polled_at?: string | null;
            latest_snapshot?: components["schemas"]["RepoSnapshotResponse"] | null;
            /** Linked Goal Path */
            linked_goal_path?: string | null;
            /**
             * Poll Tier
             * @default moderate
             */
            poll_tier: string;
            /**
             * Repo Full Name
             * @default
             */
            repo_full_name: string;
        };
        /** OnboardingChat */
        OnboardingChat: {
            /** Message */
            message: string;
        };
        /** OnboardingFeedsRequest */
        OnboardingFeedsRequest: {
            /** Selected Category Ids */
            selected_category_ids: string[];
        };
        /** OnboardingFeedsResponse */
        OnboardingFeedsResponse: {
            /** Categories */
            categories: string[];
            /** Feeds Added */
            feeds_added: number;
        };
        /** OnboardingResponse */
        OnboardingResponse: {
            /**
             * Done
             * @default false
             */
            done: boolean;
            /**
             * Estimated Total
             * @default 8
             */
            estimated_total: number;
            /**
             * Goals Created
             * @default 0
             */
            goals_created: number;
            /** Message */
            message: string;
            /**
             * Turn
             * @default 0
             */
            turn: number;
        };
        /** ProfileResponse */
        ProfileResponse: {
            /**
             * Active Projects
             * @default []
             */
            active_projects: string[];
            /**
             * Aspirations
             * @default
             */
            aspirations: string;
            /**
             * Career Stage
             * @default
             */
            career_stage: string;
            /**
             * Constraints
             * @default {}
             */
            constraints: {
                [key: string]: unknown;
            };
            /**
             * Current Role
             * @default
             */
            current_role: string;
            /**
             * Fears Risks
             * @default []
             */
            fears_risks: string[];
            /**
             * Goals Long Term
             * @default
             */
            goals_long_term: string;
            /**
             * Goals Short Term
             * @default
             */
            goals_short_term: string;
            /**
             * Industries Watching
             * @default []
             */
            industries_watching: string[];
            /**
             * Interests
             * @default []
             */
            interests: string[];
            /**
             * Is Stale
             * @default false
             */
            is_stale: boolean;
            /**
             * Languages Frameworks
             * @default []
             */
            languages_frameworks: string[];
            /**
             * Learning Style
             * @default mixed
             */
            learning_style: string;
            /**
             * Location
             * @default
             */
            location: string;
            /**
             * Skills
             * @default []
             */
            skills: {
                [key: string]: unknown;
            }[];
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Technologies Watching
             * @default []
             */
            technologies_watching: string[];
            /** Updated At */
            updated_at?: string | null;
            /**
             * Weekly Hours Available
             * @default 5
             */
            weekly_hours_available: number;
        };
        /** ProfileStatus */
        ProfileStatus: {
            /**
             * Has Api Key
             * @default false
             */
            has_api_key: boolean;
            /**
             * Has Own Key
             * @default false
             */
            has_own_key: boolean;
            /**
             * Has Profile
             * @default false
             */
            has_profile: boolean;
            /**
             * Is Stale
             * @default false
             */
            is_stale: boolean;
            /**
             * Using Shared Key
             * @default false
             */
            using_shared_key: boolean;
        };
        /** ProfileUpdate */
        ProfileUpdate: {
            /** Active Projects */
            active_projects?: string[] | null;
            /** Aspirations */
            aspirations?: string | null;
            /** Career Stage */
            career_stage?: string | null;
            /** Constraints */
            constraints?: {
                [key: string]: unknown;
            } | null;
            /** Current Role */
            current_role?: string | null;
            /** Fears Risks */
            fears_risks?: string[] | null;
            /** Goals Long Term */
            goals_long_term?: string | null;
            /** Goals Short Term */
            goals_short_term?: string | null;
            /** Industries Watching */
            industries_watching?: string[] | null;
            /** Interests */
            interests?: string[] | null;
            /** Languages Frameworks */
            languages_frameworks?: string[] | null;
            /** Learning Style */
            learning_style?: string | null;
            /** Location */
            location?: string | null;
            /** Skills */
            skills?: {
                [key: string]: unknown;
            }[] | null;
            /** Technologies Watching */
            technologies_watching?: string[] | null;
            /** Weekly Hours Available */
            weekly_hours_available?: number | null;
        };
        /** ProgressUpdate */
        ProgressUpdate: {
            /** Chapter Id */
            chapter_id: string;
            /** Guide Id */
            guide_id: string;
            /** Reading Time Seconds */
            reading_time_seconds?: number | null;
            /** Scroll Position */
            scroll_position?: number | null;
            status?: components["schemas"]["ChapterStatus"] | null;
        };
        /** QuickCapture */
        QuickCapture: {
            /** Content */
            content: string;
        };
        /** QuizSubmission */
        QuizSubmission: {
            /** Answers */
            answers: {
                [key: string]: string;
            };
        };
        /** RSSFeedAdd */
        RSSFeedAdd: {
            /** Name */
            name?: string | null;
            /** Url */
            url: string;
        };
        /** RSSFeedRemove */
        RSSFeedRemove: {
            /** Url */
            url: string;
        };
        /** ReasoningTrace */
        ReasoningTrace: {
            /**
             * Caveats
             * @default
             */
            caveats: string;
            /**
             * Confidence
             * @default 0.5
             */
            confidence: number;
            /**
             * Profile Match
             * @default
             */
            profile_match: string;
            /**
             * Source Signal
             * @default
             */
            source_signal: string;
        };
        /** RecommendationActionCreate */
        RecommendationActionCreate: {
            /** Blockers */
            blockers?: string[] | null;
            /** Due Window */
            due_window?: string | null;
            /** Effort */
            effort?: string | null;
            /** Goal Path */
            goal_path?: string | null;
            /** Next Step */
            next_step?: string | null;
            /** Objective */
            objective?: string | null;
            /** Success Criteria */
            success_criteria?: string | null;
        };
        /** RecommendationActionItem */
        RecommendationActionItem: {
            /** Blockers */
            blockers?: string[];
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Due Window
             * @default this_week
             */
            due_window: string;
            /**
             * Effort
             * @default medium
             */
            effort: string;
            /** Goal Path */
            goal_path?: string | null;
            /** Goal Title */
            goal_title?: string | null;
            /**
             * Next Step
             * @default
             */
            next_step: string;
            /**
             * Objective
             * @default
             */
            objective: string;
            /** Review Notes */
            review_notes?: string | null;
            /**
             * Status
             * @default accepted
             */
            status: string;
            /**
             * Success Criteria
             * @default
             */
            success_criteria: string;
            /**
             * Updated At
             * @default
             */
            updated_at: string;
        };
        /** RecommendationActionUpdate */
        RecommendationActionUpdate: {
            /** Blockers */
            blockers?: string[] | null;
            /** Due Window */
            due_window?: string | null;
            /** Effort */
            effort?: string | null;
            /** Goal Path */
            goal_path?: string | null;
            /** Next Step */
            next_step?: string | null;
            /** Review Notes */
            review_notes?: string | null;
            /** Status */
            status?: string | null;
            /** Success Criteria */
            success_criteria?: string | null;
        };
        /** RecommendationFeedbackRequest */
        RecommendationFeedbackRequest: {
            /** Comment */
            comment?: string | null;
            /** Rating */
            rating: number;
        };
        /** RecommendationOutcomeOverrideRequest */
        RecommendationOutcomeOverrideRequest: {
            /**
             * Note
             * @default
             */
            note: string;
            /** State */
            state: string;
        };
        /** RecommendationOutcomeResponse */
        RecommendationOutcomeResponse: {
            /**
             * Confidence
             * @default 0
             */
            confidence: number;
            /**
             * Evidence
             * @default []
             */
            evidence: {
                [key: string]: unknown;
            }[];
            /**
             * Source Summary
             * @default
             */
            source_summary: string;
            /**
             * State
             * @default unresolved
             */
            state: string;
            /**
             * User Overridden
             * @default false
             */
            user_overridden: boolean;
        };
        /** RegulatoryAlertResponse */
        RegulatoryAlertResponse: {
            /**
             * Change Type
             * @default
             */
            change_type: string;
            /** Effective Date */
            effective_date?: string | null;
            /**
             * Id
             * @default 0
             */
            id: number;
            /**
             * Metadata
             * @default {}
             */
            metadata: {
                [key: string]: unknown;
            };
            /**
             * Observed At
             * @default
             */
            observed_at: string;
            /**
             * Relevance
             * @default 0
             */
            relevance: number;
            /**
             * Source Family
             * @default
             */
            source_family: string;
            /**
             * Source Url
             * @default
             */
            source_url: string;
            /**
             * Summary
             * @default
             */
            summary: string;
            /**
             * Target Key
             * @default
             */
            target_key: string;
            /**
             * Title
             * @default
             */
            title: string;
            /**
             * Urgency
             * @default
             */
            urgency: string;
        };
        /** RepoSnapshotResponse */
        RepoSnapshotResponse: {
            /**
             * Ci Status
             * @default none
             */
            ci_status: string;
            /**
             * Commits 30D
             * @default 0
             */
            commits_30d: number;
            /**
             * Contributors 30D
             * @default 0
             */
            contributors_30d: number;
            /** Latest Release */
            latest_release?: string | null;
            /**
             * Open Issues
             * @default 0
             */
            open_issues: number;
            /**
             * Open Prs
             * @default 0
             */
            open_prs: number;
            /** Pushed At */
            pushed_at?: string | null;
            /** Snapshot At */
            snapshot_at?: string | null;
            /** Weekly Commits */
            weekly_commits?: number[];
        };
        /** RepoSummaryResponse */
        RepoSummaryResponse: {
            /**
             * Full Name
             * @default
             */
            full_name: string;
            /**
             * Html Url
             * @default
             */
            html_url: string;
            /** Language */
            language?: string | null;
            /**
             * Name
             * @default
             */
            name: string;
            /**
             * Open Issues Count
             * @default 0
             */
            open_issues_count: number;
            /**
             * Private
             * @default false
             */
            private: boolean;
            /** Pushed At */
            pushed_at?: string | null;
        };
        /** ReviewGradeRequest */
        ReviewGradeRequest: {
            /** Answer */
            answer: string;
            /** Self Grade */
            self_grade?: number | null;
        };
        /**
         * SettingsResponse
         * @description Settings with bool mask for secrets (never raw keys).
         */
        SettingsResponse: {
            /**
             * Eventbrite Token Set
             * @default false
             */
            eventbrite_token_set: boolean;
            /**
             * Feature Company Movement Enabled
             * @default false
             */
            feature_company_movement_enabled: boolean;
            /**
             * Feature Entity Extraction Enabled
             * @default true
             */
            feature_entity_extraction_enabled: boolean;
            /**
             * Feature Extended Thinking
             * @default true
             */
            feature_extended_thinking: boolean;
            /**
             * Feature Github Monitoring
             * @default false
             */
            feature_github_monitoring: boolean;
            /**
             * Feature Heartbeat Enabled
             * @default false
             */
            feature_heartbeat_enabled: boolean;
            /**
             * Feature Hiring Signals Enabled
             * @default false
             */
            feature_hiring_signals_enabled: boolean;
            /**
             * Feature Memory Enabled
             * @default true
             */
            feature_memory_enabled: boolean;
            /**
             * Feature Recommendations Enabled
             * @default false
             */
            feature_recommendations_enabled: boolean;
            /**
             * Feature Regulatory Signals Enabled
             * @default false
             */
            feature_regulatory_signals_enabled: boolean;
            /**
             * Feature Research Enabled
             * @default false
             */
            feature_research_enabled: boolean;
            /**
             * Feature Threads Enabled
             * @default true
             */
            feature_threads_enabled: boolean;
            /**
             * Feature Trending Radar Enabled
             * @default true
             */
            feature_trending_radar_enabled: boolean;
            /** Github Pat Hint */
            github_pat_hint?: string | null;
            /**
             * Github Pat Set
             * @default false
             */
            github_pat_set: boolean;
            /** Github Token Hint */
            github_token_hint?: string | null;
            /**
             * Github Token Set
             * @default false
             */
            github_token_set: boolean;
            /**
             * Has Own Key
             * @default false
             */
            has_own_key: boolean;
            /**
             * Has Profile
             * @default false
             */
            has_profile: boolean;
            /** Llm Api Key Hint */
            llm_api_key_hint?: string | null;
            /**
             * Llm Api Key Set
             * @default false
             */
            llm_api_key_set: boolean;
            /**
             * Llm Council Enabled
             * @default true
             */
            llm_council_enabled: boolean;
            /**
             * Llm Council Ready
             * @default false
             */
            llm_council_ready: boolean;
            /** Llm Custom Providers */
            llm_custom_providers?: components["schemas"]["CustomProviderInfo"][];
            /** Llm Model */
            llm_model?: string | null;
            /** Llm Provider */
            llm_provider?: string | null;
            /** Llm Provider Keys */
            llm_provider_keys?: components["schemas"]["LLMProviderKeyStatus"][];
            /** Tavily Api Key Hint */
            tavily_api_key_hint?: string | null;
            /**
             * Tavily Api Key Set
             * @default false
             */
            tavily_api_key_set: boolean;
            /**
             * Using Shared Key
             * @default false
             */
            using_shared_key: boolean;
        };
        /**
         * SettingsUpdate
         * @description Update user settings / API keys.
         */
        SettingsUpdate: {
            /** Eventbrite Token */
            eventbrite_token?: string | null;
            /** Feature Company Movement Enabled */
            feature_company_movement_enabled?: boolean | null;
            /** Feature Entity Extraction Enabled */
            feature_entity_extraction_enabled?: boolean | null;
            /** Feature Extended Thinking */
            feature_extended_thinking?: boolean | null;
            /** Feature Github Monitoring */
            feature_github_monitoring?: boolean | null;
            /** Feature Heartbeat Enabled */
            feature_heartbeat_enabled?: boolean | null;
            /** Feature Hiring Signals Enabled */
            feature_hiring_signals_enabled?: boolean | null;
            /** Feature Memory Enabled */
            feature_memory_enabled?: boolean | null;
            /** Feature Recommendations Enabled */
            feature_recommendations_enabled?: boolean | null;
            /** Feature Regulatory Signals Enabled */
            feature_regulatory_signals_enabled?: boolean | null;
            /** Feature Research Enabled */
            feature_research_enabled?: boolean | null;
            /** Feature Threads Enabled */
            feature_threads_enabled?: boolean | null;
            /** Feature Trending Radar Enabled */
            feature_trending_radar_enabled?: boolean | null;
            /** Github Pat */
            github_pat?: string | null;
            /** Github Token */
            github_token?: string | null;
            /** Llm Api Key */
            llm_api_key?: string | null;
            /** Llm Api Key Claude */
            llm_api_key_claude?: string | null;
            /** Llm Api Key Gemini */
            llm_api_key_gemini?: string | null;
            /** Llm Api Key Openai */
            llm_api_key_openai?: string | null;
            /** Llm Council Enabled */
            llm_council_enabled?: boolean | null;
            llm_custom_provider_add?: components["schemas"]["CustomProviderCreate"] | null;
            llm_custom_provider_update?: components["schemas"]["CustomProviderUpdate"] | null;
            /** Llm Custom Providers Remove */
            llm_custom_providers_remove?: string[];
            /** Llm Model */
            llm_model?: string | null;
            /** Llm Provider */
            llm_provider?: string | null;
            /** Llm Remove Providers */
            llm_remove_providers?: string[];
            /** Tavily Api Key */
            tavily_api_key?: string | null;
        };
        /**
         * SuggestionItem
         * @description Unified suggestion — either from daily brief or recommendations.
         */
        SuggestionItem: {
            /**
             * Action
             * @default
             */
            action: string;
            /**
             * Description
             * @default
             */
            description: string;
            /**
             * Kind
             * @default
             */
            kind: string;
            /** Payload */
            payload?: {
                [key: string]: unknown;
            } | null;
            /**
             * Priority
             * @default 0
             */
            priority: number;
            /**
             * Score
             * @default 0
             */
            score: number;
            /**
             * Source
             * @default
             */
            source: string;
            /**
             * Title
             * @default
             */
            title: string;
            /** Why Now */
            why_now?: {
                [key: string]: unknown;
            }[] | null;
        };
        /** ThreadDetail */
        ThreadDetail: {
            /**
             * Entries
             * @default []
             */
            entries: components["schemas"]["ThreadEntryItem"][];
            /**
             * Entry Count
             * @default 0
             */
            entry_count: number;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Label
             * @default
             */
            label: string;
        };
        /** ThreadEntryItem */
        ThreadEntryItem: {
            /**
             * Entry Date
             * @default
             */
            entry_date: string;
            /**
             * Entry Id
             * @default
             */
            entry_id: string;
            /**
             * Similarity
             * @default 0
             */
            similarity: number;
        };
        /** ThreadInboxDetail */
        ThreadInboxDetail: {
            /**
             * Available Actions
             * @default {}
             */
            available_actions: {
                [key: string]: unknown;
            };
            /**
             * Entries
             * @default []
             */
            entries: components["schemas"]["ThreadEntryItem"][];
            /**
             * Entry Count
             * @default 0
             */
            entry_count: number;
            /**
             * First Date
             * @default
             */
            first_date: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Inbox State
             * @default active
             */
            inbox_state: string;
            /**
             * Label
             * @default
             */
            label: string;
            /**
             * Last Action
             * @default
             */
            last_action: string;
            /**
             * Last Date
             * @default
             */
            last_date: string;
            /** Linked Dossier Id */
            linked_dossier_id?: string | null;
            /** Linked Goal Path */
            linked_goal_path?: string | null;
            /**
             * Recent Snippets
             * @default []
             */
            recent_snippets: string[];
            /**
             * Status
             * @default active
             */
            status: string;
        };
        /** ThreadInboxStateUpdate */
        ThreadInboxStateUpdate: {
            /** Inbox State */
            inbox_state: string;
            /**
             * Last Action
             * @default
             */
            last_action: string;
            /** Linked Dossier Id */
            linked_dossier_id?: string | null;
            /** Linked Goal Path */
            linked_goal_path?: string | null;
        };
        /** ThreadInboxSummary */
        ThreadInboxSummary: {
            /**
             * Entry Count
             * @default 0
             */
            entry_count: number;
            /**
             * First Date
             * @default
             */
            first_date: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Inbox State
             * @default active
             */
            inbox_state: string;
            /**
             * Label
             * @default
             */
            label: string;
            /**
             * Last Action
             * @default
             */
            last_action: string;
            /**
             * Last Date
             * @default
             */
            last_date: string;
            /** Linked Dossier Id */
            linked_dossier_id?: string | null;
            /** Linked Goal Path */
            linked_goal_path?: string | null;
            /**
             * Recent Snippets
             * @default []
             */
            recent_snippets: string[];
            /**
             * Status
             * @default active
             */
            status: string;
        };
        /** ThreadSummary */
        ThreadSummary: {
            /**
             * Entry Count
             * @default 0
             */
            entry_count: number;
            /**
             * First Date
             * @default
             */
            first_date: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Label
             * @default
             */
            label: string;
            /**
             * Last Date
             * @default
             */
            last_date: string;
            /**
             * Status
             * @default active
             */
            status: string;
        };
        /** TraceDetail */
        TraceDetail: {
            /** Entries */
            entries?: {
                [key: string]: unknown;
            }[];
            /**
             * From Line
             * @default 0
             */
            from_line: number;
            /** Session Id */
            session_id: string;
        };
        /** TraceListItem */
        TraceListItem: {
            /** Created At */
            created_at: number;
            /** Session Id */
            session_id: string;
            /** Size Bytes */
            size_bytes: number;
        };
        /** TrackedRecommendationAction */
        TrackedRecommendationAction: {
            action_item: components["schemas"]["RecommendationActionItem"];
            /**
             * Category
             * @default
             */
            category: string;
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Recommendation Id
             * @default
             */
            recommendation_id: string;
            /**
             * Recommendation Status
             * @default
             */
            recommendation_status: string;
            /**
             * Recommendation Title
             * @default
             */
            recommendation_title: string;
            /**
             * Score
             * @default 0
             */
            score: number;
        };
        /** UsageModelStats */
        UsageModelStats: {
            /**
             * Estimated Cost Usd
             * @default 0
             */
            estimated_cost_usd: number;
            /**
             * Input Tokens
             * @default 0
             */
            input_tokens: number;
            /** Model */
            model: string;
            /**
             * Output Tokens
             * @default 0
             */
            output_tokens: number;
            /**
             * Query Count
             * @default 0
             */
            query_count: number;
        };
        /** UsageStatsResponse */
        UsageStatsResponse: {
            /** By Model */
            by_model?: components["schemas"]["UsageModelStats"][];
            /**
             * Days
             * @default 30
             */
            days: number;
            /**
             * Total Estimated Cost Usd
             * @default 0
             */
            total_estimated_cost_usd: number;
            /**
             * Total Queries
             * @default 0
             */
            total_queries: number;
        };
        /** UserMe */
        UserMe: {
            /** Email */
            email?: string | null;
            /** Name */
            name?: string | null;
        };
        /** UserMeUpdate */
        UserMeUpdate: {
            /** Name */
            name?: string | null;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** WatchlistItem */
        WatchlistItem: {
            /**
             * Aliases
             * @default []
             */
            aliases: string[];
            /**
             * Created At
             * @default
             */
            created_at: string;
            /**
             * Domain
             * @default
             */
            domain: string;
            /**
             * Geographies
             * @default []
             */
            geographies: string[];
            /**
             * Github Org
             * @default
             */
            github_org: string;
            /**
             * Goal
             * @default
             */
            goal: string;
            /**
             * Id
             * @default
             */
            id: string;
            /**
             * Kind
             * @default theme
             */
            kind: string;
            /**
             * Label
             * @default
             */
            label: string;
            /**
             * Linked Dossier Ids
             * @default []
             */
            linked_dossier_ids: string[];
            /**
             * Priority
             * @default medium
             */
            priority: string;
            /**
             * Source Preferences
             * @default []
             */
            source_preferences: string[];
            /**
             * Tags
             * @default []
             */
            tags: string[];
            /**
             * Ticker
             * @default
             */
            ticker: string;
            /**
             * Time Horizon
             * @default quarter
             */
            time_horizon: string;
            /**
             * Topics
             * @default []
             */
            topics: string[];
            /**
             * Updated At
             * @default
             */
            updated_at: string;
            /**
             * Why
             * @default
             */
            why: string;
        };
        /** WatchlistUpsert */
        WatchlistUpsert: {
            /**
             * Aliases
             * @default []
             */
            aliases: string[];
            /**
             * Domain
             * @default
             */
            domain: string;
            /**
             * Geographies
             * @default []
             */
            geographies: string[];
            /**
             * Github Org
             * @default
             */
            github_org: string;
            /**
             * Goal
             * @default
             */
            goal: string;
            /**
             * Kind
             * @default theme
             */
            kind: string;
            /** Label */
            label: string;
            /**
             * Linked Dossier Ids
             * @default []
             */
            linked_dossier_ids: string[];
            /**
             * Priority
             * @default medium
             */
            priority: string;
            /**
             * Source Preferences
             * @default []
             */
            source_preferences: string[];
            /**
             * Tags
             * @default []
             */
            tags: string[];
            /**
             * Ticker
             * @default
             */
            ticker: string;
            /**
             * Time Horizon
             * @default quarter
             */
            time_horizon: string;
            /**
             * Topics
             * @default []
             */
            topics: string[];
            /**
             * Why
             * @default
             */
            why: string;
        };
        /** WeeklyPlanResponse */
        WeeklyPlanResponse: {
            /**
             * Capacity Points
             * @default 0
             */
            capacity_points: number;
            /**
             * Generated At
             * @default
             */
            generated_at: string;
            /** Items */
            items?: components["schemas"]["TrackedRecommendationAction"][];
            /**
             * Remaining Points
             * @default 0
             */
            remaining_points: number;
            /**
             * Used Points
             * @default 0
             */
            used_points: number;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    get_stats_api_admin_stats_get: {
        parameters: {
            query?: {
                days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ask_advisor_api_advisor_ask_post: {
        parameters: {
            query?: {
                use_tools?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdvisorAsk"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdvisorResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ask_advisor_stream_api_advisor_ask_stream_post: {
        parameters: {
            query?: {
                use_tools?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdvisorAsk"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_chat_attachment_api_advisor_attachments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_chat_attachment_api_advisor_attachments_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatAttachmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_chat_attachment_api_advisor_attachments__attachment_id__save_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                attachment_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatAttachmentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_user_conversations_api_advisor_conversations_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationListItem"][];
                };
            };
        };
    };
    get_user_conversation_api_advisor_conversations__conv_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conv_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConversationDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_user_conversation_api_advisor_conversations__conv_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                conv_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_advisor_traces_api_advisor_traces_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TraceListItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_advisor_trace_api_advisor_traces__session_id__get: {
        parameters: {
            query?: {
                from_line?: number;
            };
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TraceDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_assumptions_api_assumptions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"][];
                };
            };
        };
    };
    create_assumption_api_assumptions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssumptionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_assumption_api_assumptions__assumption_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assumption_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssumptionUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_assumption_api_assumptions__assumption_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assumption_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_assumption_api_assumptions__assumption_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assumption_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resolve_assumption_api_assumptions__assumption_id__resolve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assumption_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssumptionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_briefing_api_briefing_get: {
        parameters: {
            query?: {
                max_recommendations?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BriefingResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_pre_reading_api_curriculum_chapters__chapter_id__pre_reading_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_related_chapters_api_curriculum_chapters__chapter_id__related_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_guides_api_curriculum_guides_get: {
        parameters: {
            query?: {
                category?: string | null;
                origin?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_archived_guides_api_curriculum_guides_archived_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    generate_user_guide_api_curriculum_guides_generate_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuideGenerationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_guide_api_curriculum_guides__guide_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_user_guide_api_curriculum_guides__guide_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    launch_applied_assessment_api_curriculum_guides__guide_id__assessments__assessment_type__launch_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
                assessment_type: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_applied_assessment_api_curriculum_guides__guide_id__assessments__assessment_type__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
                assessment_type: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_chapter_api_curriculum_guides__guide_id__chapters__chapter_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    enroll_guide_api_curriculum_guides__guide_id__enroll_post: {
        parameters: {
            query?: {
                create_goal?: boolean;
            };
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    extend_guide_api_curriculum_guides__guide_id__extend_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuideExtensionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_placement_api_curriculum_guides__guide_id__placement_generate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_placement_api_curriculum_guides__guide_id__placement_submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QuizSubmission"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_user_guide_api_curriculum_guides__guide_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guide_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_next_recommendation_api_curriculum_next_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    update_progress_api_curriculum_progress_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProgressUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_quiz_api_curriculum_quiz__chapter_id__generate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_quiz_api_curriculum_quiz__chapter_id__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QuizSubmission"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_ready_guides_api_curriculum_ready_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_due_reviews_api_curriculum_review_due_get: {
        parameters: {
            query?: {
                guide_id?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_retry_reviews_api_curriculum_review_retry_get: {
        parameters: {
            query?: {
                guide_id?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    grade_review_api_curriculum_review__review_id__grade_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewGradeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_stats_api_curriculum_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    sync_content_api_curriculum_sync_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    generate_teachback_api_curriculum_teachback__chapter_id__generate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                chapter_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    grade_teachback_api_curriculum_teachback__review_id__grade_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                review_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReviewGradeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_today_learning_workflow_api_curriculum_today_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_tracks_api_curriculum_tracks_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_skill_tree_api_curriculum_tree_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_dossier_escalations_api_dossier_escalations_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DossierEscalationResponse"][];
                };
            };
        };
    };
    accept_dossier_escalation_api_dossier_escalations__escalation_id__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                escalation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DossierEscalationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dismiss_dossier_escalation_api_dossier_escalations__escalation_id__dismiss_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                escalation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DossierEscalationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    snooze_dossier_escalation_api_dossier_escalations__escalation_id__snooze_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                escalation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DossierEscalationSnoozeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DossierEscalationResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    post_engagement_api_engagement_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EngagementEvent"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    engagement_stats_api_engagement_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EngagementStats"];
                };
            };
        };
    };
    export_user_data_api_export_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_user_repos_api_github_repos_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepoSummaryResponse"][];
                };
            };
        };
    };
    monitor_repo_api_github_repos_monitor_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MonitorRepoRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MonitoredRepoResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unmonitor_repo_api_github_repos_monitor__repo_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repo_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    link_goal_api_github_repos_monitor__repo_id__link_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repo_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LinkGoalRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MonitoredRepoResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_repo_api_github_repos_monitor__repo_id__refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repo_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepoSnapshotResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unlink_goal_api_github_repos_monitor__repo_id__unlink_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repo_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MonitoredRepoResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_monitored_api_github_repos_monitored_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MonitoredRepoResponse"][];
                };
            };
        };
    };
    list_goals_api_goals_get: {
        parameters: {
            query?: {
                include_inactive?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_goal_api_goals_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GoalCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_in_api_goals__filepath__check_in_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GoalCheckIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_milestone_api_goals__filepath__milestones_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MilestoneAdd"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    complete_milestone_api_goals__filepath__milestones_complete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MilestoneComplete"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_progress_api_goals__filepath__progress_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_status_api_goals__filepath__status_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GoalStatusUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_greeting_api_greeting_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GreetingResponse"];
                };
            };
        };
    };
    health_api_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_insights_api_insights_get: {
        parameters: {
            query?: {
                /** @description Filter by insight type */
                type?: string | null;
                min_severity?: number;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InsightResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_company_movements_api_intel_company_movements_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyMovementResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_company_movements_api_intel_company_movements__company_key__get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                company_key: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanyMovementResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    search_entities_api_intel_entities_get: {
        parameters: {
            query: {
                q: string;
                type?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_entity_api_intel_entities__entity_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entity_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_follow_ups_api_intel_follow_ups_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntelFollowUp"][];
                };
            };
        };
    };
    save_follow_up_api_intel_follow_ups_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FollowUpUpsert"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IntelFollowUp"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_health_api_intel_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_hiring_signals_api_intel_hiring_signals_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HiringSignalResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_hiring_signals_for_entity_api_intel_hiring_signals__entity_key__get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                entity_key: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HiringSignalResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_item_entities_api_intel_items__item_id__entities_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_intel_preferences_api_intel_preferences_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    update_intel_preferences_api_intel_preferences_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["IntelPreferencesUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_recent_api_intel_recent_get: {
        parameters: {
            query?: {
                days?: number;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_regulatory_alerts_api_intel_regulatory_alerts_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegulatoryAlertResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_regulatory_alerts_for_target_api_intel_regulatory_alerts__target_key__get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path: {
                target_key: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegulatoryAlertResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_rss_feeds_api_intel_rss_feeds_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    add_rss_feed_api_intel_rss_feeds_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RSSFeedAdd"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_rss_feed_api_intel_rss_feeds_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RSSFeedRemove"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    scrape_now_api_intel_scrape_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    search_intel_api_intel_search_get: {
        parameters: {
            query: {
                q: string;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_trending_api_intel_trending_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    list_watchlist_api_intel_watchlist_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WatchlistItem"][];
                };
            };
        };
    };
    create_watchlist_item_api_intel_watchlist_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WatchlistUpsert"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WatchlistItem"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_watchlist_item_api_intel_watchlist__item_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_watchlist_item_api_intel_watchlist__item_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WatchlistUpsert"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WatchlistItem"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_entries_api_journal_get: {
        parameters: {
            query?: {
                entry_type?: string | null;
                tag?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalEntry"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_entry_api_journal_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JournalCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalEntry"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    quick_capture_api_journal_quick_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QuickCapture"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalEntry"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_entry_api_journal__filepath__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalEntry"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_entry_api_journal__filepath__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["JournalUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalEntry"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_entry_api_journal__filepath__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_entry_mind_map_api_journal__filepath__mind_map_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalMindMapEnvelope"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_entry_mind_map_api_journal__filepath__mind_map_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JournalMindMapEnvelope"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_entry_receipt_api_journal__filepath__receipt_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                filepath: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExtractionReceiptEnvelope"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_reports_api_library_reports_get: {
        parameters: {
            query?: {
                search?: string | null;
                status?: string | null;
                collection?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportListItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_report_api_library_reports_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LibraryReportCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_report_pdf_api_library_reports_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_report_pdf_api_library_reports_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_report_api_library_reports__report_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_report_api_library_reports__report_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LibraryReportUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_report_api_library_reports__report_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_report_file_api_library_reports__report_id__file_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_report_api_library_reports__report_id__refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_report_api_library_reports__report_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LibraryReportResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_facts_api_memory_facts_get: {
        parameters: {
            query?: {
                category?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MemoryFact"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_fact_api_memory_facts__fact_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                fact_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MemoryFact"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_fact_api_memory_facts__fact_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                fact_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_stats_api_memory_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MemoryStats"];
                };
            };
        };
    };
    list_notifications_api_notifications_get: {
        parameters: {
            query?: {
                limit?: number;
                unread_only?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    notification_count_api_notifications_count_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    mark_all_read_api_notifications_read_all_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    mark_read_api_notifications__notification_id__read_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                notification_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    chat_onboarding_api_onboarding_chat_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OnboardingChat"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OnboardingResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_feed_categories_api_onboarding_feed_categories_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeedCategoryItem"][];
                };
            };
        };
    };
    set_onboarding_feeds_api_onboarding_feeds_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OnboardingFeedsRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OnboardingFeedsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_profile_status_api_onboarding_profile_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProfileStatus"];
                };
            };
        };
    };
    start_onboarding_api_onboarding_start_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OnboardingResponse"];
                };
            };
        };
    };
    track_page_view_api_page_view_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    [key: string]: unknown;
                };
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_profile_api_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProfileResponse"];
                };
            };
        };
    };
    update_profile_api_profile_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfileUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_ideas_api_projects_ideas_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_issues_api_projects_issues_get: {
        parameters: {
            query?: {
                limit?: number;
                days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_recommendations_api_recommendations_get: {
        parameters: {
            query?: {
                search?: string | null;
                category?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BriefingRecommendation"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_action_items_api_recommendations_actions_get: {
        parameters: {
            query?: {
                status?: string | null;
                goal_path?: string | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackedRecommendationAction"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    weekly_plan_api_recommendations_weekly_plan_get: {
        parameters: {
            query?: {
                capacity_points?: number;
                goal_path?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WeeklyPlanResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_action_item_api_recommendations__rec_id__action_item_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationActionUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackedRecommendationAction"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_action_item_api_recommendations__rec_id__action_item_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationActionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TrackedRecommendationAction"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_recommendation_feedback_api_recommendations__rec_id__feedback_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationFeedbackRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BriefingRecommendation"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_recommendation_outcome_api_recommendations__rec_id__outcome_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rec_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationOutcomeResponse"] | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    override_recommendation_outcome_api_recommendations__rec_id__outcome_override_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rec_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationOutcomeOverrideRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationOutcomeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_dossiers_api_research_dossiers_get: {
        parameters: {
            query?: {
                include_archived?: boolean;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_dossier_api_research_dossiers_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DossierCreateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_dossier_api_research_dossiers__dossier_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                dossier_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_dossier_api_research_dossiers__dossier_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                dossier_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_research_api_research_run_post: {
        parameters: {
            query?: {
                topic?: string | null;
                dossier_id?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_topics_api_research_topics_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_settings_api_settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettingsResponse"];
                };
            };
        };
    };
    update_settings_api_settings_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SettingsUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettingsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    test_custom_provider_api_settings_test_custom_provider_post: {
        parameters: {
            query: {
                provider_id: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    test_llm_connectivity_api_settings_test_llm_post: {
        parameters: {
            query?: {
                provider?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_usage_api_settings_usage_get: {
        parameters: {
            query?: {
                days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UsageStatsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_suggestions_api_suggestions_get: {
        parameters: {
            query?: {
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SuggestionItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_threads_api_threads_get: {
        parameters: {
            query?: {
                min_entries?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThreadSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_thread_inbox_api_threads_inbox_get: {
        parameters: {
            query?: {
                state?: string | null;
                query?: string;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThreadInboxSummary"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reindex_threads_api_threads_reindex_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_thread_api_threads__thread_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThreadDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    make_goal_from_thread_api_threads__thread_id__actions_make_goal_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_research_from_thread_api_threads__thread_id__actions_run_research_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_dossier_from_thread_api_threads__thread_id__actions_start_dossier_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_thread_state_api_threads__thread_id__state_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ThreadInboxStateUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ThreadInboxDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_api_user_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserMe"];
                };
            };
        };
    };
    delete_me_api_user_me_delete: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    update_me_api_user_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserMeUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserMe"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_metrics_metrics_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
