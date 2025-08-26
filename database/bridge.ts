import {
  createAgent,
  getAgentById,
  getAgentByName,
  listAgents,
  updateAgent,
  deleteAgent,
  initAgents,
} from "./repositories/agents";
import {
  createSystemEvent,
  listSystemEvents,
  listSystemEventsByType,
  initSystemEvents,
} from "./repositories/events";
import {
  createInstance,
  getInstanceById,
  listInstances,
  updateInstance,
} from "./repositories/instances";
import {
  createMessage,
  listMessagesByInstance,
} from "./repositories/messages";

const [, , action, payloadJson] = process.argv;

async function main() {
  const payload = payloadJson ? JSON.parse(payloadJson) : {};
  switch (action) {
    case "list":
      console.log(JSON.stringify(await listAgents()));
      break;
    case "get":
      console.log(JSON.stringify(await getAgentById(payload.id)));
      break;
    case "get_by_name":
      console.log(JSON.stringify(await getAgentByName(payload.name)));
      break;
    case "create":
      console.log(JSON.stringify(await createAgent(payload)));
      break;
    case "update":
      console.log(
        JSON.stringify(await updateAgent(payload.id, payload.data))
      );
      break;
    case "delete":
      console.log(JSON.stringify(await deleteAgent(payload.id)));
      break;
    case "init":
      await initAgents();
      console.log("null");
      break;
    case "log_event":
      console.log(JSON.stringify(await createSystemEvent(payload)));
      break;
    case "list_events":
      console.log(JSON.stringify(await listSystemEvents()));
      break;
    case "list_events_by_type":
      console.log(
        JSON.stringify(await listSystemEventsByType(payload.type))
      );
      break;
    case "init_events":
      await initSystemEvents();
      console.log("null");
      break;
    case "create_instance":
      console.log(JSON.stringify(await createInstance(payload)));
      break;
    case "get_instance":
      console.log(JSON.stringify(await getInstanceById(payload.id)));
      break;
    case "list_instances":
      console.log(JSON.stringify(await listInstances()));
      break;
    case "update_instance":
      console.log(
        JSON.stringify(await updateInstance(payload.id, payload.data))
      );
      break;
    case "create_message":
      console.log(JSON.stringify(await createMessage(payload)));
      break;
    case "list_messages_by_instance":
      console.log(
        JSON.stringify(await listMessagesByInstance(payload.instanceId))
      );
      break;
    default:
      console.error(`Unknown action: ${action}`);
      process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
