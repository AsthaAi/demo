"""
Audit Logger for ShopperAI
Handles logging of all agent activities and transactions.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


class AuditLogger:
    """Logger for auditing agent activities"""

    def __init__(self, logger_name: str):
        """Initialize the audit logger"""
        self.logger_name = logger_name
        self.logs_dir = os.path.join('shopping', 'logs')
        self._ensure_logs_directory()

    def _ensure_logs_directory(self):
        """Ensure the logs directory exists"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            print(f"✅ Created logs directory at {self.logs_dir}")

    def _write_log(self, log_type: str, data: Dict[str, Any]):
        """Write a log entry to the appropriate log file"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "logger": self.logger_name,
            "type": log_type,
            **data
        }

        log_file = os.path.join(self.logs_dir, f"{log_type}.log")
        try:
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            print(f"❌ Failed to write to log file {log_file}: {str(e)}")

    def log_access_verification(
        self,
        agent_id: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log access verification attempts"""
        self._write_log('access', {
            "agent_id": agent_id,
            "action": action,
            "status": status,
            "details": details or {}
        })

    def log_risk_analysis(
        self,
        transaction_id: str,
        risk_level: str,
        analysis_details: Dict[str, Any],
        agent_id: str
    ):
        """Log risk analysis results"""
        self._write_log('risk', {
            "transaction_id": transaction_id,
            "risk_level": risk_level,
            "analysis_details": analysis_details,
            "agent_id": agent_id
        })

    def log_suspicious_activity(
        self,
        flag_id: str,
        transaction_id: str,
        reason: str,
        agent_id: str
    ):
        """Log suspicious activity flags"""
        self._write_log('suspicious', {
            "flag_id": flag_id,
            "transaction_id": transaction_id,
            "reason": reason,
            "agent_id": agent_id
        })

    def log_agent_communication(
        self,
        source_agent_id: str,
        target_agent_id: str,
        communication_type: str,
        message: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log agent communications"""
        self._write_log('communication', {
            "source_agent_id": source_agent_id,
            "target_agent_id": target_agent_id,
            "type": communication_type,
            "message": message,
            "status": status,
            "details": details or {}
        })

    def get_communication_statistics(
        self,
        agent_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about agent communications"""
        stats = {
            "total_communications": 0,
            "successful_communications": 0,
            "failed_communications": 0,
            "unique_targets": set(),
            "communication_types": {}
        }

        try:
            log_file = os.path.join(self.logs_dir, 'communication.log')
            if not os.path.exists(log_file):
                return stats

            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        if log['source_agent_id'] == agent_id:
                            # Filter by time if specified
                            if start_time and log['timestamp'] < start_time:
                                continue
                            if end_time and log['timestamp'] > end_time:
                                continue

                            stats['total_communications'] += 1
                            if log['status'] == 'success':
                                stats['successful_communications'] += 1
                            else:
                                stats['failed_communications'] += 1

                            stats['unique_targets'].add(log['target_agent_id'])
                            comm_type = log['type']
                            stats['communication_types'][comm_type] = stats['communication_types'].get(
                                comm_type, 0) + 1
                    except json.JSONDecodeError:
                        continue

            # Convert set to list for JSON serialization
            stats['unique_targets'] = list(stats['unique_targets'])

        except Exception as e:
            print(f"❌ Error getting communication statistics: {str(e)}")

        return stats

    def get_agent_communications(
        self,
        agent_id: str,
        communication_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> list:
        """Get detailed communication logs for an agent"""
        communications = []

        try:
            log_file = os.path.join(self.logs_dir, 'communication.log')
            if not os.path.exists(log_file):
                return communications

            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        if log['source_agent_id'] == agent_id:
                            # Apply filters
                            if communication_type and log['type'] != communication_type:
                                continue
                            if start_time and log['timestamp'] < start_time:
                                continue
                            if end_time and log['timestamp'] > end_time:
                                continue

                            communications.append(log)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"❌ Error getting agent communications: {str(e)}")

        return communications
