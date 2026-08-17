export * from './events.service';
import { EventsService } from './events.service';
export * from './events.serviceInterface';
export * from './health.service';
import { HealthService } from './health.service';
export * from './health.serviceInterface';
export const APIS = [EventsService, HealthService];
