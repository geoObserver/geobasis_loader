from datetime import datetime
from typing import Any, Optional

from .catalog_models import (
	Catalog,
	CatalogIndex,
	CatalogIndexEntry,
	CatalogSource,
	EntryType,
	Region,
	ServiceType,
	Topic,
	TopicCombination,
	TopicEntry,
	TopicGroup,
)


def _entry_common(data: dict[str, Any]) -> dict[str, Any]:
	return {
		"id": data["id"],
		"title": data["title"],
		"description": data.get("description"),
		"deprecated": data.get("deprecated", False),
		"deprecated_message": data.get("deprecated_message"),
		"keywords": frozenset(data.get("keywords", [])),
		"separator_after": data.get("separator_after", False),
	}


def _resolve_template(
    id: str,
	server_value: Any,
	pattern_value: Any,
	layer_id: Optional[str],
	server_uris: dict[str, str],
	uri_patterns: dict[str, str],
) -> Optional[str]:
	if not server_value or not pattern_value:
		return None

	if not isinstance(server_value, str) or not isinstance(pattern_value, str):
		raise ValueError(
			f"Invalid service template for topic '{id}': "
			f"server_value and pattern_value must be strings"
		)

	server_uri = server_uris.get(server_value, server_value)
	pattern = uri_patterns.get(pattern_value, pattern_value)
	if layer_id is None:
		raise ValueError(
			f"Incomplete service template for topic '{id}'"
		)

	return pattern.format(uri=server_uri, layer_id=layer_id, crs="{crs}")


def load_topic(
	data: dict[str, Any],
	global_crs: frozenset[str],
	server_uris: dict[str, str],
	uri_patterns: dict[str, str],
) -> Topic:
	id = data.get("id", "")
	service_type = ServiceType(data["service_type"])
	server_uri = data.get("server_uri")
	uri_pattern = data.get("uri_pattern")
	layer_id = data.get("layer_id")
	service_uri = data.get("service_uri") or _resolve_template(
		data.get("id", ""), server_uri, uri_pattern, layer_id, server_uris, uri_patterns
	)
	if service_uri is None:
		raise ValueError(f"Topic '{id}' has no service URI")

	if "{layer_id}" in service_uri or "{uri}" in service_uri:
		raise ValueError(f"URI for topic '{id}' must not contain '{{layer_id}}' or '{{uri}}'")
	
	if service_type == ServiceType.WEB:
		if "{crs}" in service_uri:
			raise ValueError(f"URI for topic '{id}' must not contain '{{crs}}' for WEB service type")
	else:
		if "{crs}" not in service_uri:
			raise ValueError(f"URI for topic '{id}' must contain '{{crs}}' for non-WEB service types")

	local_crs = frozenset(data.get("crs", []))
	crs = local_crs.union(global_crs)

	return Topic(
		**_entry_common(data),
		crs=crs,
		uri=service_uri,
		service_uri=data.get("service_uri"),
		server_uri=server_uri if server_uri else None,
		uri_pattern=uri_pattern if uri_pattern else None,
		layer_id=data.get("layer_id"),
		service_type=service_type,
		opacity=data.get("opacity", 1.0),
		min_scale=data.get("min_scale"),
		max_scale=data.get("max_scale"),
		fill_color=data.get("fill_color", [220, 220, 220]),
		stroke_color=data.get("stroke_color", "black"),
		stroke_width=data.get("stroke_width", 0.3),
	)


def load_entry(
	data: dict[str, Any],
	global_crs: frozenset[str],
	server_uris: dict[str, str],
	uri_patterns: dict[str, str],
) -> TopicEntry:
	local_crs = frozenset(data.get("crs", []))
	crs = local_crs.union(global_crs)
	entry_type = data.get("entry_type")
	if entry_type == EntryType.TOPIC.value:
		return load_topic(data, global_crs, server_uris, uri_patterns)
	if entry_type == EntryType.TOPIC_GROUP.value:
		subtopics = [
			load_topic(value, global_crs, server_uris, uri_patterns)
			for value in data.get("subtopics", [])
		]
		return TopicGroup(
			**_entry_common(data),
			crs=crs,
			subtopics=subtopics,
		)
	if entry_type == EntryType.TOPIC_COMBINATION.value:
		return TopicCombination(
			**_entry_common(data),
			crs=crs,
			references=frozenset(data.get("references", [])),
		)
	raise ValueError(f"Unknown entry type: {entry_type}")


def load_catalog(data: dict[str, Any]) -> Catalog:
	service_templates = data.get("service_templates", {})
	server_uris = {}
	uri_patterns = {}
	# if "server_uris" in service_templates or "uri_patterns" in service_templates:
	server_uris.update(service_templates.get("server_uris", {}))
	uri_patterns.update(service_templates.get("uri_patterns", {}))
	# else:
	# 	for template_name, template in service_templates.items():
	# 		server_uris.update(template.get("server_uris", {}))
	# 		if "uri_pattern" in template:
	# 			uri_patterns[template_name] = template["uri_pattern"]

	global_crs = frozenset(data.get("global_crs", []))
	regions = []
	for region_data in data.get("regions", []):
		topics = [
			load_entry(value, global_crs, server_uris, uri_patterns)
			for value in region_data.get("topics", [])
		]
		regions.append(Region(
			id=region_data["id"],
			title=region_data["title"],
			topics=topics,
			separator_after=region_data.get("separator_after", False),
		))

	catalog = Catalog(
		id=data["id"],
		title=data["title"],
		modified=datetime.fromisoformat(data["modified"]),
		format_version=data.get("format_version", 7.0),
		global_crs=global_crs,
		author=data["author"],
		description=data.get("description"),
		server_uris=server_uris,
		uri_patterns=uri_patterns,
		regions=regions,
	)
	catalog.build_index()
	return catalog

# FILEDS LIKE MODIFIED IN ENTRIES UNUSED, EMPTY FILEDS WRITTEN EVEN THOUGH THEY SHOULD JUST NOT APPEAR -> NO ROUND TRIP 

# def dump_entry(entry: TopicEntry, global_crs: frozenset) -> dict[str, Any]:
# 	data = {
# 		"id": entry.id,
# 		"title": entry.title,
# 		"entry_type": entry.entry_type.value,
# 		"description": entry.description,
# 		"deprecated": entry.deprecated,
# 		"deprecated_message": entry.deprecated_message,
# 		"keywords": sorted(entry.keywords),
# 		"separator_after": entry.separator_after,
# 	}
# 	crs = sorted(entry.crs.difference(global_crs))
# 	if isinstance(entry, Topic):
# 		data.update({
# 			"service_type": entry.service_type.value,
# 			"opacity": entry.opacity,
# 			"min_scale": entry.min_scale,
# 			"max_scale": entry.max_scale,
# 		})
#		if entry.service_type != ServiceType.WEB:
#			data["crs"] = crs
#
# 		if entry.service_uri:
# 			data["service_uri"] = entry.service_uri
# 		else:
# 			data["server_uri"] = entry.server_uri
# 			data["uri_pattern"] = entry.uri_pattern
# 			data["layer_id"] = entry.layer_id
# 		if entry.is_vector():
# 			data.update({
# 				"fill_color": entry.fill_color,
# 				"stroke_color": entry.stroke_color,
# 				"stroke_width": entry.stroke_width,
# 			})
# 	elif isinstance(entry, TopicGroup):
# 		data["crs"] = crs
# 		data["subtopics"] = {key: dump_entry(topic, global_crs) for key, topic in entry.subtopics.items()}
# 	elif isinstance(entry, TopicCombination):
# 		data["crs"] = crs
# 		data["references"] = sorted(entry.references)
# 	return data

# FILEDS LIKE LEGAL_NOTICE IN CATLAOG UNUSED -> NO ROUND TRIP 

# def dump_catalog(catalog: Catalog) -> dict[str, Any]:
# 	return {
# 		"format_version": catalog.format_version,
# 		"id": catalog.id,
# 		"title": catalog.title,
# 		"modified": catalog.modified.isoformat(timespec="seconds"),
# 		"author": catalog.author,
# 		"description": catalog.description,
# 		"global_crs": sorted(catalog.global_crs),
# 		"service_templates": {
# 			"server_uris": catalog.server_uris,
# 			"uri_patterns": catalog.uri_patterns,
# 		},
# 		"regions": {
# 			key: {
# 				"title": region.title,
# 				"separator_after": region.separator_after,
# 				"topics": {topic_key: dump_entry(topic, catalog.global_crs) for topic_key, topic in region.topics.items()},
# 			}
# 			for key, region in catalog.regions.items()
# 		},
# 	}


def load_catalog_index(data: dict[str, Any]) -> CatalogIndex:
	return CatalogIndex(
		catalog_source=CatalogSource(data["catalog_source"]),
		modified=datetime.fromisoformat(data["modified"]),
		format_version=data.get("format_version", 7.0),
		catalogs=[CatalogIndexEntry(
            id=entry["id"],
            title=entry["title"],
            file=entry["file"],
            author=entry.get("author"),
            description=entry.get("description"),
            modified=datetime.fromisoformat(entry["modified"]) if entry.get("modified") else None,
        ) 
        for entry in data.get("catalogs", [])],
	)


# def dump_catalog_index(index: CatalogIndex) -> dict[str, Any]:
# 	return {
# 		"format_version": index.format_version,
# 		"catalog_source": index.catalog_source.value,
# 		"modified": index.modified.isoformat(timespec="seconds"),
# 		"catalogs": [
# 			{
# 				"id": entry.id,
# 				"title": entry.title,
# 				"file": entry.file,
# 				"author": entry.author,
# 				"description": entry.description,
# 				"modified": entry.modified.isoformat(timespec="seconds") if entry.modified else None,
# 			}
# 			for entry in index.catalogs
# 		],
# 	}