// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {BinaryField} from "@web/views/fields/binary/binary_field";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

export class PreviewRecordField extends BinaryField {
    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
        this.action = useService("action");
    }

    onFilePreview() {
        const attachmentData = {
            id: this.props.record.resId,
            filename: this.props.record.data.display_name || "",
            name: this.props.record.data.display_name || "",
            mimetype: this.props.record.data.mimetype,
            model_name: this.props.record.resModel,
            displayName: this.props.record.data.display_name || "",
            defaultSource: `/web/content?id=${this.props.record.resId}&field=content&model=dms.file&filename_field=name`,
        };
        
        const openWithAction = () => {
            this.action.doAction({
                type: 'ir.actions.act_url',
                url: attachmentData.defaultSource,
                target: 'new',
            });
        };

        try {
            const AttachmentModel = this.store?.Attachment || this.store?.models?.Attachment;
            if (AttachmentModel && typeof AttachmentModel.insert === 'function') {
                const attachment = AttachmentModel.insert(attachmentData);
                this.fileViewer.open(attachment);
            } else {
                openWithAction();
            }
        } catch (e) {
            openWithAction();
        }
    }
}

PreviewRecordField.template = "dms.FilePreviewField";
PreviewRecordField.props = {
    ...standardFieldProps,
};

const previewRecordField = {
    component: PreviewRecordField,
    displayName: _t("Preview Record"),
    supportedTypes: ["binary"],
    extractProps: () => {
        return {};
    },
};
registry.category("fields").add("preview_binary", previewRecordField);
