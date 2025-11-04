import type {LearningPath, Module, PreferencesCreate} from "@/types/learning-paths";
import type {PersonalTeamStatisticsApiResponse, TeamDashboardApiResponse} from "@/types/team-statistics";
import type {
    QuizAttempt,
    QuizForTaking,
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizResult,
    QuizSubmission
} from "@/types/quiz";
import {GenerationResponse} from "@/types/path-generation";
import {UserStatistics} from "@/types/user-statistics";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "http://localhost:8001/api/v1";

// API Error handler
class APIError extends Error {
    constructor(message: string, public status?: number, public data?: any) {
        super(message);
        this.name = 'APIError';
    }
}

// Helper function to get auth headers
function getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    const headers: HeadersInit = {
        "Content-Type": "application/json"
    };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    
    return headers;
}

// Helper function to handle API responses
async function handleResponse(response: Response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle authentication errors
        if (response.status === 401) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
            throw new APIError("Authentication required", 401, errorData);
        }
        
        throw new APIError(
            errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            errorData
        );
    }
    // Handle "204 No Content" response by returning a success object
    if (response.status === 204) {
        return { success: true, message: "Operation completed successfully." };
    }
    return response.json();
}

export const api = {
    // Authentication endpoints
    sendMagicLink: async (email: string) => {
        const response = await fetch(`${BASE_URL}/auth/send-magic-link`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        return handleResponse(response);
    },

    verifyMagicLink: async (token: string) => {
        const response = await fetch(`${BASE_URL}/auth/verify-magic-link`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token }),
        });
        return handleResponse(response);
    },

    getCurrentUser: async () => {
        const response = await fetch(`${BASE_URL}/auth/me`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    validateToken: async () => {
        const response = await fetch(`${BASE_URL}/auth/validate-token`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    logout: async () => {
        const response = await fetch(`${BASE_URL}/auth/logout`, {
            method: "POST",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    refreshToken: async () => {
        const response = await fetch(`${BASE_URL}/auth/refresh-token`, {
            method: "POST",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },


    // Learning Path Management
    getLearningPath: async (learningPathId: number): Promise<{ learning_path: LearningPath; modules: Module[] }> => {
        const response = await fetch(`${BASE_URL}/learning-paths/${learningPathId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    // User Learning Paths
    getUserLearningPaths: async (userId: string): Promise<LearningPath[]> => {
        const url = `${BASE_URL}/learning-paths/user/${userId}`;
        const response = await fetch(url, {
            headers: getAuthHeaders(),
        });
        return await handleResponse(response);
    },

    deleteLearningPath: async (learningPathId: number) => {
        const response = await fetch(`${BASE_URL}/learning-paths/${learningPathId}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },
    
    getLearningPathPreferences: async (learningPathId: number) => {
        const response = await fetch(`${BASE_URL}/learning-paths/${learningPathId}/preferences`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    // Mark module as complete
    markModuleComplete: async (moduleId: number, userId?: string, timeSpentMinutes: number = 0) => {
        try {
            const currentUserId = userId || localStorage.getItem('currentUserId');
            if (!currentUserId) {
                throw new Error("User ID is required to mark module as complete");
            }
            
            const requestBody = {
                user_id: currentUserId,
                time_spent_minutes: timeSpentMinutes
            };

            const response = await fetch(`${BASE_URL}/modules/${moduleId}/complete`, {
                method: "PUT",
                headers: {
                    ...getAuthHeaders(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody)
            });

            return await handleResponse(response);
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(error instanceof Error ? error.message : "Failed to mark module as complete", 500,error);
        }
    },

    getLearningPathProgress: async (userId: string, learningPathId: number) => {
        const response = await fetch(`${BASE_URL}/learning-paths/${learningPathId}/users/${userId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getUserStatistics: async (userId: string): Promise<UserStatistics> => {
        const response = await fetch(`${BASE_URL}/users/${userId}/statistics`, {
            headers: getAuthHeaders(),
        });

        const result = await handleResponse(response);

        // The endpoint should now return all UserStatistics fields in a single call
        // Ensure the response contains all expected fields from UserStatistics interface
        return {
            user_id: result.user_id || userId,

            // Streak fields
            streak_days: result.streak_days || 0,
            user_created_at: result.user_created_at || null,

            // Content Completion fields
            completed_learning_paths: result.completed_learning_paths || 0,
            modules_completed: result.modules_completed || 0,
            skill_points_earned: result.skill_points_earned || 0,
            quizzes_completed: result.quizzes_completed || 0,

            // Where you stand
            user_total_minutes: result.user_total_minutes || 0,
            community_average_minutes: result.community_average_minutes || 0,

            // Daily Learning Data
            learning_time_data: result.learning_time_data || {},

            // Platform Time Summary
            platform_time_summary: result.platform_time_summary || {},

            // Key Insights fields
            top_percentile_time: result.top_percentile_time,
            community_impact: result.community_impact,
            content_coverage: result.content_coverage,
        };
    },

    getQuizForModule: async (moduleId: number): Promise<QuizForTaking> => {
        const response = await fetch(`${BASE_URL}/quizzes/module/${moduleId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    generateQuiz: async (request: QuizGenerationRequest): Promise<QuizGenerationResponse> => {
        const response = await fetch(`${BASE_URL}/quizzes/generate`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(request),
        });
        return handleResponse(response);
    },

    // Quiz Attempts
    startQuizAttempt: async (quizId: number, userId: string): Promise<QuizAttempt> => {
        const response = await fetch(`${BASE_URL}/quizzes/${quizId}/start-quiz?user_id=${userId}`, {
            method: "POST",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },


    submitQuizAttempt: async (quizId: number, userId: string, submission: QuizSubmission): Promise<QuizResult> => {
        const response = await fetch(`${BASE_URL}/quizzes/${quizId}/submit?user_id=${userId}`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(submission),
        });
        return handleResponse(response);
    },

    getUserQuizAttemptsByModule: async (moduleId: number, userId: string): Promise<QuizAttempt[]> => {
        const response = await fetch(`${BASE_URL}/quizzes/attempts/module/${moduleId}?user_id=${userId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getQuizAttemptDetails: async (attemptId: number) => {
        const response = await fetch(`${BASE_URL}/quizzes/attempts/${attemptId}/details`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    startTeamLearningPathGeneration: async (preferences: PreferencesCreate & { team_id: string }): Promise<GenerationResponse> => {
        const response = await fetch(
            `${BASE_URL}/path-generation/generate`,
            {
                method: "POST",
                headers: getAuthHeaders(),
                body: JSON.stringify(preferences),
            }
        );
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            if (response.status === 401) {
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
                throw new APIError("Authentication required", 401, errorData);
            }
            throw new APIError(`Failed to generate team learning path: ${response.statusText}`, response.status);
        }
        return await response.json();
    },

    // Learning Path Generation
    startLearningPathGeneration: async (preferences: PreferencesCreate): Promise<GenerationResponse> => {
        const response = await fetch(
            `${BASE_URL}/path-generation/generate`,
            {
                method: "POST",
                headers: getAuthHeaders(),
                body: JSON.stringify(preferences),
            }
        );
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            if (response.status === 401) {
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
                throw new APIError("Authentication required", 401, errorData);
            }
            throw new APIError(`Failed to generate learning path: ${response.statusText}`, response.status);
        }
        return await response.json();
    },


    insertBridgeModule: async (
        learningPathId: number,
        insertPosition: number,
        userId: string | number,
        customRequirements: string = "",
        generateQuiz: boolean = true,
        platformName: string | null = null
    ) => {
        const body = {
            learning_path_id: learningPathId,
            insert_position: insertPosition,
            platform_name: platformName || "youtube",
            user_query: customRequirements
        };
        const response = await fetch(
            `${BASE_URL}/module-insertion/insert`,
            {
                method: "POST",
                headers: getAuthHeaders(),
                body: JSON.stringify(body)
            }
        );
        return handleResponse(response);
    },

    getMyTasks: async () => {
        const response = await fetch(`${BASE_URL}/path-generation/my-tasks`, {
            headers: getAuthHeaders(),
        });
        return await handleResponse(response);
    },

    // =============================
    // COMPLETE TEAM FUNCTIONALITY
    // =============================

    getMyTeams: async () => {
        const response = await fetch(`${BASE_URL}/teams/my-teams`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getTeam: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    createTeam: async (teamData: any) => {
        const response = await fetch(`${BASE_URL}/teams/`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(teamData),
        });
        return handleResponse(response);
    },

    updateTeam: async (teamId: string, teamData: any) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify(teamData),
        });
        return handleResponse(response);
    },

    deleteTeam: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    generateJoinCode: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/join-code`, {
            method: "POST",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    joinTeamByCode: async (joinData: { join_code: string }) => {
        const response = await fetch(`${BASE_URL}/teams/join`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(joinData),
        });
        return handleResponse(response);
    },

    getTeamMembers: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/members`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    removeTeamMember: async (teamId: string, userId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/members/${userId}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    kickTeamMember: async (teamId: string, userId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/members/${userId}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    updateMemberRole: async (teamId: string, userId: string, role: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/members/${userId}/role`, {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({ role }),
        });
        return handleResponse(response);
    },

    getTeamLearningPaths: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/learning-paths/team/${teamId}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    deleteTeamLearningPath: async (teamId: string, learningPathId: number) => {
        // Use the regular learning path deletion endpoint
        const response = await fetch(`${BASE_URL}/learning-paths/${learningPathId}`, {
            method: "DELETE",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getTeamStatistics: async (teamId: string) => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/statistics`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getNotifications: async (params: {
        include_read?: boolean;
        include_deleted?: boolean;
        page?: number;
        per_page?: number;
    } = {}) => {
        const searchParams = new URLSearchParams();
        if (params.include_read !== undefined) searchParams.append('include_read', params.include_read.toString());
        if (params.include_deleted !== undefined) searchParams.append('include_deleted', params.include_deleted.toString());
        if (params.page !== undefined) searchParams.append('page', params.page.toString());
        if (params.per_page !== undefined) searchParams.append('per_page', params.per_page.toString());
        
        const response = await fetch(`${BASE_URL}/notifications/?${searchParams}`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    markNotificationAsRead: async (notificationId: number) => {
        const response = await fetch(`${BASE_URL}/notifications/${notificationId}`, {
            method: "PATCH",
            headers: getAuthHeaders(),
            body: JSON.stringify({ is_read: true }),
        });
        return handleResponse(response);
    },

    markAllNotificationsAsRead: async () => {
        const response = await fetch(`${BASE_URL}/notifications/mark-all-read`, {
            method: "POST",
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },

    getTeamStatisticsView: async (teamId: string): Promise<TeamDashboardApiResponse | PersonalTeamStatisticsApiResponse> => {
        const response = await fetch(`${BASE_URL}/teams/${teamId}/personal`, {
            headers: getAuthHeaders(),
        });
        return handleResponse(response);
    },


};

export const teamApi = {
    getMyTeams: api.getMyTeams,
    getTeam: api.getTeam,
    createTeam: api.createTeam,
    updateTeam: api.updateTeam,
    deleteTeam: api.deleteTeam,
    generateJoinCode: api.generateJoinCode,
    joinTeamByCode: api.joinTeamByCode,
    getTeamMembers: api.getTeamMembers,
    getTeamLearningPaths: api.getTeamLearningPaths,
    deleteTeamLearningPath: api.deleteTeamLearningPath,
    getTeamStatistics: api.getTeamStatistics,
    removeTeamMember: api.removeTeamMember,
    kickTeamMember: api.kickTeamMember,
    updateMemberRole: api.updateMemberRole,
    startLearningPathGeneration: api.startLearningPathGeneration,
    startTeamLearningPathGeneration: api.startTeamLearningPathGeneration,
    getMyTasks: api.getMyTasks,
};


