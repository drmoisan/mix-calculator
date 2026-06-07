"""Presenter for the tabbed schema-builder dialog (Feature D, AC4/AC5).

This presenter drives a passive :class:`SchemaBuilderViewProtocol`. It holds the
in-progress schema as plain :mod:`src.gui.presenters._schema_builder_state` data,
coordinates the per-tab edits, validates runtime formula entry through the
Feature C :class:`~src.schema_formula.FormulaEvaluator`, renders a Preview by
applying the in-progress schema through the schema service's loader, and persists
the assembled schema through the
:class:`~src.gui.services.schema_service.SchemaServiceProtocol`.

Responsibilities:
    - Mirror the view's edits into the in-progress state.
    - Validate a formula expression against the known column set, surfacing
      :class:`~src.schema_formula.FormulaError` inline (and clearing it on
      success).
    - Build a Preview by assembling the schema and running the service's loader.
    - Assemble and save the schema, surfacing model
      :class:`~src.schema_model.SchemaValidationError` as an error.

Scope boundaries:
    - No Qt import. Formula validation routes through Feature C only; no new
      dependency. Persistence flows only through the service/registry boundary.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from src.gui.presenters._schema_builder_state import (
    SchemaBuilderState,
    assemble_schema,
    known_column_names,
    parse_key_pattern,
)
from src.schema_formula import FormulaError
from src.schema_model import SchemaValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.gui.protocols import SchemaBuilderViewProtocol
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.schema_formula import FormulaEvaluator
    from src.schema_model import ColumnSpec, SchemaDefinition

__all__ = ["SchemaBuilderPresenter"]

logger = logging.getLogger(__name__)


class SchemaBuilderPresenter:
    """Coordinate authoring and saving a schema across the builder tabs.

    Purpose:
        Translate the schema-builder dialog's per-tab edits into an in-progress
        schema, validate formula entry through Feature C, drive the Preview, and
        persist the assembled schema, keeping all logic out of the Qt dialog.

    Responsibilities:
        Hold the in-progress state; sync identity/columns/key/dedup/derived edits;
        validate a formula against the known column set (surfacing or clearing an
        inline error); build a Preview frame via the service's loader; and
        assemble and save the schema, surfacing structural validation errors. It
        does not import Qt and persists only through the service.

    Usage:
        Constructed with a :class:`SchemaBuilderViewProtocol` view, a
        :class:`SchemaServiceProtocol`, and an optional
        :class:`~src.schema_formula.FormulaEvaluator`. Route the dialog's edit
        and action signals to the presenter methods.

    Attributes:
        _view: The schema-builder view this presenter drives.
        _service: The schema service used for preview loaders and persistence.
        _evaluator: The Feature C evaluator used to validate formula entry.
        _state: The in-progress schema state.
    """

    def __init__(
        self,
        view: SchemaBuilderViewProtocol,
        service: SchemaServiceProtocol,
        *,
        formula_evaluator: FormulaEvaluator | None = None,
    ) -> None:
        """Initialize the presenter with its view, service, and evaluator.

        Args:
            view: The passive schema-builder view to drive.
            service: The schema service used for the preview loader and saving.
            formula_evaluator: The evaluator used to validate formula entry. When
                ``None``, a default :class:`~src.schema_formula.FormulaEvaluator`
                is created.
        """
        self._view = view
        self._service = service
        # A default evaluator is created lazily to avoid importing the concrete
        # class at module load when a caller injects its own.
        if formula_evaluator is None:
            from src.schema_formula import FormulaEvaluator as _FormulaEvaluator

            formula_evaluator = _FormulaEvaluator()
        self._evaluator = formula_evaluator
        self._state = SchemaBuilderState()

    def seed_from_caller(
        self,
        *,
        required_specs: Sequence[ColumnSpec] | None = None,
        optional_specs: Sequence[ColumnSpec] | None = None,
        default_key_pattern: str | None = None,
        preview_slice: PreviewSlice | None = None,
    ) -> None:
        """Seed the in-progress state from the per-tab caller's build inputs.

        Populates the column rows from the supplied required and optional specs
        (required first, then optional), parses ``default_key_pattern`` into
        ordered structured key parts, and records the masked preview slice and its
        header columns as the draggable source-column pool. The builder reads only
        the supplied slice and performs no I/O (Decision 5). All arguments are
        optional so the blank menu path (no inputs) leaves the state empty.

        Args:
            required_specs: The source's required column specs, or ``None``.
            optional_specs: The source's optional column specs, or ``None``.
            default_key_pattern: The default key pattern to parse into structured
                parts, or ``None`` to leave the key empty.
            preview_slice: The masked preview slice the builder reads, or ``None``.

        Returns:
            ``None``.

        Side effects:
            Replaces the in-progress state's column rows, key parts, source-column
            pool, and preview slice, then renders the state to the view.
        """
        # Build the column rows required-first then optional so the Columns tab
        # lists required columns ahead of optional ones, matching display order.
        required = list(required_specs or ())
        optional = list(optional_specs or ())
        all_specs = [*required, *optional]
        columns = [self._spec_to_row(spec) for spec in all_specs]
        # Carry each caller column's expected dtype so the Columns tab can render
        # the expected type and the dtype check can target it.
        column_dtypes = {spec.canonical_name: spec.expected_dtype for spec in all_specs}
        # Parse the default pattern into ordered structured parts; an absent
        # pattern leaves the key empty for the user to compose.
        key_parts = (
            parse_key_pattern(default_key_pattern) if default_key_pattern else []
        )
        # The masked slice header is the draggable source-column pool; the builder
        # reads only this slice and never touches a reader or the filesystem.
        source_columns = list(preview_slice.header) if preview_slice else []
        self._state = SchemaBuilderState(
            columns=columns,
            column_dtypes=column_dtypes,
            key_parts=key_parts,
            key_columns=tuple(p.value for p in key_parts if p.is_column_ref),
            source_columns=source_columns,
            preview_slice=preview_slice,
        )
        self._render_state()

    @staticmethod
    def _spec_to_row(spec: ColumnSpec) -> tuple[str, str, bool, bool, tuple[str, ...]]:
        """Convert a caller column spec into a builder column row tuple.

        Args:
            spec: The caller-supplied column spec.

        Returns:
            A ``(canonical_name, role, required, in_output, aliases)`` row tuple
            mirroring the state's column-row shape. ``in_output`` carries the
            spec's output-membership flag through the builder.
        """
        return (
            spec.canonical_name,
            spec.role,
            spec.required,
            spec.in_output,
            spec.aliases,
        )

    @property
    def state(self) -> SchemaBuilderState:
        """Return the current in-progress builder state.

        Exposed read-only so wiring and tests can inspect the seeded/loaded state
        (column rows, structured key parts, source-column pool, preview slice)
        without driving it through the view.

        Returns:
            The presenter's current :class:`SchemaBuilderState`.
        """
        return self._state

    def load_existing(self, name: str) -> None:
        """Load an existing schema into the in-progress state and render it.

        Args:
            name: The schema name to load from the service.

        Returns:
            ``None``.

        Side effects:
            Reads the schema via the service and pushes its fields to the view.
        """
        schema = self._service.load_schema(name)
        self._state = self._state_from_schema(schema)
        self._render_state()

    def add_derived(self, name: str, expression: str) -> None:
        """Append a derived column to the in-progress state in order.

        Called when the Derived-tab dialog is accepted (Decision 7). The new
        derived column is appended after existing derived columns so ordering is
        preserved, and the state is re-rendered so the column becomes referenceable
        on the Columns and Key tabs.

        Args:
            name: The derived column's canonical name.
            expression: The derived column's formula expression.

        Returns:
            ``None``.

        Side effects:
            Appends to the state's derived list and re-renders the state.
        """
        self._state.derived.append((name, expression))
        self._render_state()

    def new_from_template(self, template_name: str) -> None:
        """Seed fresh state from the closest-existing schema as a template.

        Loads ``template_name`` and copies its column specs (including persisted
        aliases), structured key, and dedup policy into a new in-progress state,
        but clears the name so the user adjusts and saves the result under a new
        name (Decision 6). The template file is never overwritten because the
        seeded name is blank until the user provides a new one and saves.

        Args:
            template_name: The name of the closest-existing schema to seed from.

        Returns:
            ``None``.

        Side effects:
            Reads the template schema via the service and renders the seeded
            state to the view.
        """
        template = self._service.load_schema(template_name)
        state = self._state_from_schema(template)
        # Clear identity so save-as writes a new file rather than overwriting the
        # template; the user supplies the new name before saving.
        state.name = ""
        self._state = state
        self._render_state()

    @staticmethod
    def _state_from_schema(schema: SchemaDefinition) -> SchemaBuilderState:
        """Build an in-progress state mirroring a loaded schema.

        Carries the loaded schema's structured key parts (column-ref and
        literal-text, preserving order), aggregate/collapse dedup mode and
        discriminator, and the column rows into editable state so a subsequent
        edit-and-save round-trips faithfully.

        Args:
            schema: The loaded schema definition.

        Returns:
            A :class:`SchemaBuilderState` populated from ``schema``.
        """
        return SchemaBuilderState(
            name=schema.name,
            version=schema.version,
            description=schema.description,
            columns=[
                (c.canonical_name, c.role, c.required, c.in_output, c.aliases)
                for c in schema.columns
            ],
            # Carry each column's expected dtype so the Columns tab can render it
            # and an edit-then-save preserves the declared type.
            column_dtypes={c.canonical_name: c.expected_dtype for c in schema.columns},
            key_columns=schema.key.column_names,
            # Preserve the full structured key (including literal-text parts) so
            # an edit-then-save re-emits the same composition, not just the
            # column-ref names.
            key_parts=list(schema.key.parts),
            sku_coercion=schema.key.sku_coercion,
            dedup_mode=schema.dedup.mode,
            discriminator=schema.dedup.discriminator_column,
            derived=[(d.name, d.expression) for d in schema.derived_columns],
        )

    def _render_state(self) -> None:
        """Push the entire in-progress state to the view.

        Returns:
            ``None``.

        Side effects:
            Calls every view setter with the current state.
        """
        self._view.set_identity(
            self._state.name, self._state.version, self._state.description
        )
        self._view.set_columns(list(self._state.columns))
        self._view.set_key(self._state.key_columns, self._state.sku_coercion)
        self._view.set_dedup(self._state.dedup_mode, self._state.discriminator)
        self._view.set_derived(list(self._state.derived))
        self._push_structured_key_and_dtypes()

    def _push_structured_key_and_dtypes(self) -> None:
        """Push structured key parts and per-column dtypes when the view supports it.

        The structured key-part and expected-dtype setters are newer additions to
        the view contract. They are invoked through ``getattr`` so a view that has
        not yet adopted them (for example a minimal test fake) is unaffected, while
        a view that implements them receives the ordered parts and per-column type.

        Returns:
            ``None``.

        Side effects:
            Calls ``view.set_key_parts`` and ``view.set_column_dtypes`` when those
            methods exist on the view.
        """
        set_key_parts = getattr(self._view, "set_key_parts", None)
        # Render the full structured key (including literal-text parts) so the Key
        # tab shows interleaved literals, not only the column-ref names.
        if callable(set_key_parts):
            set_key_parts([(p.kind, p.value) for p in self._state.key_parts])
        set_column_dtypes = getattr(self._view, "set_column_dtypes", None)
        # Render the per-column expected dtype in declared column order.
        if callable(set_column_dtypes):
            set_column_dtypes(
                [
                    (canonical, self._state.column_dtypes.get(canonical))
                    for canonical, _role, _required, _in_output, _aliases in (
                        self._state.columns
                    )
                ]
            )

    def sync_from_view(self) -> None:
        """Read every editable field from the view into the in-progress state.

        Returns:
            ``None``.

        Side effects:
            Updates the in-progress state from the view's getters.
        """
        name, version, description = self._view.get_identity()
        self._state.name = name
        self._state.version = version
        self._state.description = description
        self._state.columns = list(self._view.get_columns())
        key_columns, sku_coercion = self._view.get_key()
        self._state.key_columns = key_columns
        self._state.sku_coercion = sku_coercion
        dedup_mode, discriminator = self._view.get_dedup()
        self._state.dedup_mode = dedup_mode
        self._state.discriminator = discriminator
        self._state.derived = list(self._view.get_derived())

    def validate_formula(self, expression: str) -> bool:
        """Validate a derived-column formula against the known column set.

        Reads the current edits, then validates ``expression`` through the
        Feature C evaluator against the declared and derived column names. On a
        :class:`~src.schema_formula.FormulaError` the descriptive message is shown
        inline and the method returns ``False``; on success the inline error is
        cleared and the method returns ``True``.

        Args:
            expression: The formula source the user entered.

        Returns:
            ``True`` when the formula is valid; ``False`` otherwise.

        Side effects:
            Calls ``view.show_formula_error`` on failure or
            ``view.clear_formula_error`` on success.
        """
        self.sync_from_view()
        known = known_column_names(self._state)
        # FormulaError carries a descriptive message in args[0]; surface exactly
        # that text inline so the operator sees the construct/column at fault.
        try:
            self._evaluator.validate(expression, known)
        except FormulaError as error:
            message = str(error.args[0]) if error.args else str(error)
            self._view.show_formula_error(message)
            return False
        self._view.clear_formula_error()
        return True

    def update_preview(self, preview_rows: Sequence[Mapping[str, object]]) -> bool:
        """Assemble the schema and render a preview by applying its loader.

        Builds a raw frame from ``preview_rows``, assembles the in-progress schema
        (surfacing a structural error if invalid), runs the schema's loader, and
        pushes the resulting rows (rendered as strings) to the view's preview.

        Args:
            preview_rows: Raw sample rows as column-name-to-value mappings.

        Returns:
            ``True`` when a preview was rendered; ``False`` when assembly or load
            failed and an error was surfaced.

        Side effects:
            Calls ``view.show_preview`` on success or ``view.show_error`` on
            failure.
        """
        self.sync_from_view()
        try:
            schema = assemble_schema(self._state)
        except SchemaValidationError as error:
            self._view.show_error(str(error))
            return False

        # Apply the assembled schema through the service's loader so the Preview
        # reflects the same transform the import flow would run.
        try:
            loader = self._service.build_loader(schema)
            out = loader.load(pd.DataFrame(preview_rows))
        except (FormulaError, ValueError) as error:
            self._view.show_error(str(error))
            return False

        rows = [
            [str(value) for value in record]
            for record in out.itertuples(index=False, name=None)
        ]
        self._view.show_preview(rows)
        return True

    def save(self) -> bool:
        """Assemble and persist the in-progress schema.

        Reads the current edits, assembles the schema (surfacing a structural
        error if invalid), and persists it through the service.

        Returns:
            ``True`` when the schema was saved; ``False`` when assembly failed and
            an error was surfaced.

        Side effects:
            Calls ``service.save_schema`` on success or ``view.show_error`` on a
            structural validation failure.
        """
        self.sync_from_view()
        try:
            schema = assemble_schema(self._state)
        except SchemaValidationError as error:
            self._view.show_error(str(error))
            return False

        self._service.save_schema(schema)
        logger.info("Saved schema %r from the schema builder.", schema.name)
        return True
