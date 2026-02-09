/** useTeams Hook
 *
 * Custom hook for fetching teams (for task creation team selection)
 */

import { useState, useCallback, useEffect } from "react";
import { message } from "antd";
import type { TeamResponse } from "@/types";
import { teamApi } from "@/services/resources";

interface UseTeamsReturn {
  teams: TeamResponse[];
  loading: boolean;
  fetchTeams: () => Promise<void>;
}

export function useTeams(): UseTeamsReturn {
  const [teams, setTeams] = useState<TeamResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTeams = useCallback(async () => {
    setLoading(true);
    try {
      const response = await teamApi.list();
      setTeams(response.items);
    } catch (error) {
      message.error("Failed to fetch teams");
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  return {
    teams,
    loading,
    fetchTeams,
  };
}
