from services.api_handler_service import ApiHandlerService
from services.msg_service import MessageService


def background_tasks(username: str, api_srv: ApiHandlerService, msg_srv: MessageService):
    try:
        msg_srv.retry_unsynchronized_receipts(username)
        online_users = api_srv.get_online_users(username)
        api_srv.update_ip_address(username)
        if online_users:
            pending_mssgs_by_user = msg_srv.find_pending_mssgs_by_user(username, online_users)
            msg_srv.send_pending_mssgs(pending_mssgs_by_user, username)
    except Exception as e:
        print(f"[SyncLoop] Error: {e}")
        
def leader_search_bg(api_srv: ApiHandlerService):
    try:
        api_srv._discover_managers()
        api_srv._find_leader_addr()
    except Exception as e:
        print(f"[SyncLoop] Error: {e}")
