type FileUploadProps = {
  title: string;
  description: string;
};

export function FileUpload({ title, description }: FileUploadProps) {
  return (
    <div className="upload-zone" aria-hidden="true">
      <p className="eyebrow">Planned Shared Component</p>
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}