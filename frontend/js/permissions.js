/** Permisos de presentación, complementarios a los obligatorios del backend y MySQL. */
const planilleroActions = new Set([
  'planilla-save',
  'goal-create','goal-update','goal-delete',
  'card-create','card-update','card-delete'
]);
export function canModify(role, kind, action){
  if(role==='administrador')return true;
  if(role==='planillero')return planilleroActions.has(action);
  return false;
}
