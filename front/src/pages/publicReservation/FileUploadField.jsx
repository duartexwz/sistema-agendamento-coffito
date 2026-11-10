export function FileUploadField({ files, onChange }) {
  return (
    <div>
      <label htmlFor="publicFiles" className="form-label">
        Material de divulgacao pronto ou documentacao
      </label>
      <input
        id="publicFiles"
        className="form-control"
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.mp4,.mov"
        onChange={(event) => onChange(Array.from(event.target.files ?? []))}
      />
      <p className="field-help">Formatos planejados: PDF, DOC, DOCX, JPG, PNG, WEBP, MP4 e MOV.</p>
      {files.length > 0 && (
        <ul className="file-list">
          {files.map((file) => (
            <li key={`${file.name}-${file.size}`}>
              {file.name} <span>{formatSize(file.size)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatSize(size) {
  if (!size) return '0 KB';
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}
